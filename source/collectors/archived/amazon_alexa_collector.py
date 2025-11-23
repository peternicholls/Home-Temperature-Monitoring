#!/usr/bin/env python3
"""
Amazon Alexa Unified Collector

Collects data from ALL Amazon/Alexa smart home devices in a single efficient cycle:
- Amazon Smart Air Quality Monitors (temperature, humidity, PM2.5, VOC, CO2, IAQ)
- Nest Thermostats (temperature, mode, state)
- Any other Alexa-connected devices with temperature sensors

Architecture:
- Single GraphQL call per cycle to discover ALL devices
- Parallel state API calls to fetch readings for all devices
- Automatic device type detection and routing
- Efficient cookie-based authentication (no alexapy dependency)

Sprint: 005-system-reliability
Enhancement: Unified collector to reduce API calls by 50% and eliminate rate limiting
"""

import httpx
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path

from source.utils.structured_logger import StructuredLogger


class AmazonAlexaCollector:
    """
    Unified collector for all Amazon Alexa smart home devices.
    
    Supported Device Types:
    - Amazon Smart Air Quality Monitor (AIR_QUALITY_MONITOR)
    - Nest Thermostat (THERMOSTAT)
    - Any device with temperature capability
    
    Features:
    - Single GraphQL discovery per cycle (efficient)
    - Parallel async state fetching
    - Cookie-based authentication
    - Comprehensive retry logic with rate limit handling
    - Device type auto-detection
    """
    
    # Supported device types and their GraphQL appliance types
    DEVICE_TYPE_MAP = {
        'AIR_QUALITY_MONITOR': 'alexa_aqm',
        'THERMOSTAT': 'nest_thermostat',
    }
    
    def __init__(self, cookies: Dict[str, str], config: dict = {}, logger: Optional[StructuredLogger] = None):
        """
        Initialize unified Amazon Alexa collector.
        
        Args:
            cookies: Dictionary of Amazon cookies from authentication
            config: Configuration dictionary
            logger: Optional StructuredLogger instance
        """
        self.cookies = cookies
        self.config = config or {}
        self.logger = logger
        
        if self.logger:
            self.logger.debug(f"Init collector", cookies_present=cookies is not None, config_present=config is not None)
        
        # Extract configuration
        collection_config = self.config.get('collection', {})
        self.retry_max_attempts = collection_config.get('retry_attempts', 3)
        self.retry_base_delay = collection_config.get('retry_backoff_base', 1.0)
        self.max_timeout = collection_config.get('max_timeout', 120)
        
        # Amazon API configuration
        amazon_config = self.config.get('amazon_aqm', {})
        self.domain = amazon_config.get('domain', 'alexa.amazon.co.uk')
        
        # Extract CSRF token from cookies
        self.csrf_token = cookies.get('csrf', '') if cookies else ''
        
        # Set up HTTP headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://{self.domain}/spa/index.html',
            'csrf': self.csrf_token,
        }
        
        if self.logger:
            self.logger.debug(f"Initialized Amazon Alexa Collector", domain=self.domain, cookies_count=len(cookies))
    
    async def discover_all_devices(self) -> List[Dict[str, Any]]:
        """
        Discover ALL Amazon Alexa smart home devices via single GraphQL call.
        
        Discovers:
        - Amazon Air Quality Monitors
        - Nest Thermostats
        - Any other temperature-capable devices
        
        Returns:
            List of device dictionaries with unified format
        """
        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                if self.logger:
                    self.logger.info(f"Discovering Amazon/Alexa devices", attempt=attempt, max_attempts=self.retry_max_attempts)
                
                # Single GraphQL query for ALL smart home devices
                query = """
                query CustomerSmartHome {
                    endpoints(
                        endpointsQueryParams: { paginationParams: { disablePagination: true } }
                    ) {
                        items {
                            legacyAppliance {
                                applianceId
                                applianceTypes
                                friendlyName
                                friendlyDescription
                                manufacturerName
                                modelName
                                entityId
                                capabilities
                                alexaDeviceIdentifierList {
                                    dmsDeviceSerialNumber
                                }
                            }
                        }
                    }
                }
                """
                
                url = f"https://{self.domain}/nexus/v1/graphql"
                
                async with httpx.AsyncClient(cookies=self.cookies) as client:
                    response = await client.post(
                        url,
                        json={"query": query},
                        headers=self.headers,
                        timeout=self.max_timeout
                    )
                
                # Handle rate limiting specifically
                if response.status_code == 429:
                    if self.logger:
                        self.logger.warning("Rate limit hit during device discovery", status=429)
                    
                    if attempt < self.retry_max_attempts:
                        # Rate limits need longer backoff (60 seconds)
                        wait_time = 60
                        if self.logger:
                            self.logger.info(f"Rate limit backoff", wait_seconds=wait_time)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        return []
                
                if response.status_code != 200:
                    if self.logger:
                        self.logger.error(f"GraphQL API error", status=response.status_code, response=response.text[:200])
                    
                    if attempt < self.retry_max_attempts:
                        wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        return []
                
                # Parse response
                try:
                    data = response.json()
                except Exception as json_error:
                    if self.logger:
                        self.logger.error(f"Failed to parse JSON response", error=str(json_error), response_text=response.text[:500])
                    if attempt < self.retry_max_attempts:
                        await asyncio.sleep(self.retry_base_delay * (2 ** (attempt - 1)))
                        continue
                    return []
                
                if not isinstance(data, dict) or 'data' not in data:
                    if self.logger:
                        self.logger.error("Invalid GraphQL response format", data_type=type(data).__name__, has_data_key='data' in data if isinstance(data, dict) else False)
                    if attempt < self.retry_max_attempts:
                        await asyncio.sleep(self.retry_base_delay * (2 ** (attempt - 1)))
                        continue
                    return []
                
                # Extract and categorize devices
                discovered_devices = []
                endpoints = data.get('data', {}).get('endpoints', {}).get('items', [])
                
                if self.logger:
                    self.logger.debug(f"Processing {len(endpoints)} endpoints from GraphQL response")
                
                for item in endpoints:
                    if not isinstance(item, dict):
                        if self.logger:
                            self.logger.debug(f"Skipping non-dict item: {type(item)}")
                        continue
                        
                    appliance = item.get('legacyAppliance')
                    if not appliance:
                        if self.logger:
                            self.logger.debug(f"Skipping item without legacyAppliance")
                        continue
                    
                    device = self._parse_device(appliance)
                    if device:
                        discovered_devices.append(device)
                
                if self.logger:
                    device_summary = {}
                    for dev in discovered_devices:
                        dtype = dev['device_type']
                        device_summary[dtype] = device_summary.get(dtype, 0) + 1
                    
                    self.logger.info(
                        "Device discovery complete",
                        total_devices=len(discovered_devices),
                        devices_by_type=device_summary
                    )
                
                return discovered_devices
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error discovering devices", attempt=attempt, error=str(e), exc_info=True)
                
                if attempt < self.retry_max_attempts:
                    wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(wait_time)
                else:
                    return []
        
        return []
    
    def _parse_device(self, appliance: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse appliance data into unified device format.
        
        Args:
            appliance: Raw appliance data from GraphQL
            
        Returns:
            Unified device dictionary or None if not supported
        """
        if not appliance or not isinstance(appliance, dict):
            if self.logger:
                self.logger.debug(f"Skipping invalid appliance", appliance_type=type(appliance).__name__)
            return None
            
        appliance_types = appliance.get('applianceTypes', [])
        friendly_desc = appliance.get('friendlyDescription', '')
        manufacturer = appliance.get('manufacturerName', '')
        
        # Determine device type
        device_type = None
        for app_type in appliance_types:
            if app_type in self.DEVICE_TYPE_MAP:
                device_type = self.DEVICE_TYPE_MAP[app_type]
                break
        
        # Skip unsupported devices
        if not device_type:
            return None
        
        # Extract serial number
        device_serial = None
        alexa_device_ids = appliance.get('alexaDeviceIdentifierList', [])
        for device_id in alexa_device_ids:
            if isinstance(device_id, dict):
                serial = device_id.get('dmsDeviceSerialNumber')
                if serial:
                    device_serial = serial
                    break
        
        # Skip if no serial (can't create unique ID)
        if not device_serial:
            if self.logger:
                self.logger.debug(f"Skipping device without serial", name=appliance.get('friendlyName'))
            return None
        
        # Create unified device info
        device_info = {
            'device_id': f'{device_type.split("_")[0]}:{device_serial}',  # alexa:XXX or nest:XXX
            'device_type': device_type,
            'entity_id': appliance.get('entityId'),
            'appliance_id': appliance.get('applianceId'),
            'friendly_name': appliance.get('friendlyName'),
            'device_serial': device_serial,
            'manufacturer': manufacturer,
            'model_name': appliance.get('modelName', ''),
            'capabilities': appliance.get('capabilities', []),
            'appliance_types': appliance_types,
        }
        
        if self.logger:
            self.logger.debug(
                f"Parsed device",
                device_id=device_info['device_id'],
                type=device_type,
                name=device_info['friendly_name']
            )
        
        return device_info
    
    async def get_device_state(self, device: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch current state for a device from Phoenix State API.
        
        Args:
            device: Device info dictionary from discover_all_devices()
            
        Returns:
            Dict with readings or None if failed
        """
        entity_id = device['entity_id']
        device_type = device['device_type']
        
        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                url = f"https://{self.domain}/api/phoenix/state"
                payload = {
                    "stateRequests": [{
                        "entityId": entity_id,
                        "entityType": "ENTITY"
                    }]
                }
                
                async with httpx.AsyncClient(cookies=self.cookies) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=self.headers,
                        timeout=self.max_timeout
                    )
                
                # Handle rate limiting
                if response.status_code == 429:
                    if self.logger:
                        self.logger.warning("Rate limit hit fetching state", device_id=device['device_id'])
                    
                    if attempt < self.retry_max_attempts:
                        wait_time = 60  # Rate limit needs longer wait
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        return None
                
                if response.status_code != 200:
                    if self.logger:
                        self.logger.error(f"State API error", device_id=device['device_id'], status=response.status_code)
                    
                    if attempt < self.retry_max_attempts:
                        await asyncio.sleep(self.retry_base_delay * (2 ** (attempt - 1)))
                        continue
                    return None
                
                data = response.json()
                
                # Parse based on device type
                if device_type == 'alexa_aqm':
                    return self._parse_aqm_state(data, device)
                elif device_type == 'nest_thermostat':
                    return self._parse_nest_state(data, device)
                else:
                    return None
                    
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error fetching device state", device_id=device['device_id'], attempt=attempt, error=str(e))
                
                if attempt < self.retry_max_attempts:
                    await asyncio.sleep(self.retry_base_delay * (2 ** (attempt - 1)))
                else:
                    return None
        
        return None
    
    def _parse_aqm_state(self, data: Dict[str, Any], device: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Amazon AQM state data."""
        try:
            device_states = data.get('deviceStates', [])
            if not device_states:
                return None
            
            capability_states = device_states[0].get('capabilityStates', [])
            
            readings = {
                'device_id': device['device_id'],
                'device_type': device['device_type'],
                'location': device['friendly_name'],
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
            
            # Parse capability states (JSON strings)
            for cap_state in capability_states:
                name = cap_state.get('name', '')
                value_str = cap_state.get('value', '{}')
                
                try:
                    value = json.loads(value_str) if isinstance(value_str, str) else value_str
                except json.JSONDecodeError:
                    continue
                
                # Extract readings
                if name == 'temperatureSensor':
                    readings['temperature_celsius'] = value.get('value', {}).get('value')
                elif name == 'humidity':
                    readings['humidity_percent'] = value.get('value')
                elif name == 'pm25':
                    readings['pm25_ugm3'] = value.get('value')
                elif name == 'voc':
                    readings['voc_ppb'] = value.get('value')
                elif name == 'carbonMonoxideLevel':
                    readings['co_ppm'] = value.get('value')
                elif name == 'carbonDioxideLevel':
                    readings['co2_ppm'] = value.get('value')
                elif name == 'indoorAirQualityScore':
                    readings['iaq_score'] = value.get('value')
            
            return readings if 'temperature_celsius' in readings else None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error parsing AQM state", device_id=device['device_id'], error=str(e))
            return None
    
    def _parse_nest_state(self, data: Dict[str, Any], device: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Nest thermostat state data."""
        try:
            device_states = data.get('deviceStates', [])
            if not device_states:
                return None
            
            capability_states = device_states[0].get('capabilityStates', [])
            
            readings = {
                'device_id': device['device_id'],
                'device_type': device['device_type'],
                'location': device['friendly_name'],
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
            
            # Parse capability states
            for cap_state in capability_states:
                name = cap_state.get('name', '')
                value_str = cap_state.get('value', '{}')
                
                try:
                    value = json.loads(value_str) if isinstance(value_str, str) else value_str
                except json.JSONDecodeError:
                    continue
                
                # Extract readings
                if name == 'temperatureSensor':
                    temp_value = value.get('value', {})
                    if isinstance(temp_value, dict):
                        readings['temperature_celsius'] = temp_value.get('value')
                elif name == 'thermostatMode':
                    readings['thermostat_mode'] = value.get('value')
                elif name == 'thermostatState':
                    readings['thermostat_state'] = value.get('value')
            
            return readings if 'temperature_celsius' in readings else None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error parsing Nest state", device_id=device['device_id'], error=str(e))
            return None
    
    async def collect_all_readings(self) -> List[Dict[str, Any]]:
        """
        Discover and collect readings from all Amazon/Alexa devices.
        
        Returns:
            List of reading dictionaries ready for database storage
        """
        # Single discovery call for ALL devices
        devices = await self.discover_all_devices()
        
        if not devices:
            if self.logger:
                self.logger.warning("No devices discovered")
            return []
        
        # Fetch states in parallel for efficiency
        tasks = [self.get_device_state(device) for device in devices]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None and exceptions
        readings = []
        for result in results:
            if isinstance(result, dict) and result:
                readings.append(result)
            elif isinstance(result, Exception):
                if self.logger:
                    self.logger.error(f"Exception during state fetch", error=str(result))
        
        if self.logger:
            self.logger.info(f"Collection complete", total_readings=len(readings), devices_attempted=len(devices))
        
        return readings
