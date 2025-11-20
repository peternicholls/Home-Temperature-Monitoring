#!/usr/bin/env python3
"""
Amazon Alexa Air Quality Monitor Collector

Collects air quality data from Amazon Smart Air Quality Monitor using GraphQL API.
Uses cookie-based authentication (same approach as Home Assistant's Alexa Media Player).

Based on research findings from docs/Amazon-Alexa-Air-Quality-Monitoring/
"""

import logging
import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class AmazonAQMCollector:
    """
    Collector for Amazon Smart Air Quality Monitor.
    
    Features:
    - GraphQL API for device discovery
    - Cookie-based authentication (no alexapy required)
    - Temperature, humidity, PM2.5, VOC, CO2 readings
    - Retry logic with exponential backoff
    - Direct HTTP requests to Amazon APIs
    """
    
    def __init__(self, cookies: Dict[str, str], config: dict = {}):
        """
        Initialize collector with Amazon cookies.
        
        Args:
            cookies: Dictionary of Amazon cookies from authentication
            config: Configuration dictionary with retry settings
        """
        self.cookies = cookies
        self.config = config or {}
        
        # Extract configuration
        collection_config = self.config.get('collection', {})
        self.retry_max_attempts = collection_config.get('retry_attempts', 5)
        self.retry_base_delay = collection_config.get('retry_backoff_base', 1.0)
        self.max_timeout = collection_config.get('max_timeout', 120)
        
        # Amazon API configuration
        amazon_config = config.get('amazon_aqm', {})
        self.domain = amazon_config.get('domain', 'alexa.amazon.com')
        self.device_serial = amazon_config.get('device_serial')
        
        logger.debug(f"Configured domain: {self.domain}")
        logger.debug(f"Amazon config: {amazon_config}")
        
        # Extract CSRF token from cookies
        self.csrf_token = cookies.get('csrf', '')
        
        # Set up HTTP headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://{self.domain}/spa/index.html',
            'csrf': self.csrf_token,
        }
        
        # Store cookies for use with httpx
        self.cookies = cookies
        logger.debug(f"Configured {len(cookies)} cookies for domain: {self.domain}")
    
    async def list_devices(self) -> List[Dict[str, Any]]:
        """
        Discover Amazon Air Quality Monitors via GraphQL API.
        
        Uses the same GraphQL endpoint as Home Assistant's Alexa Media Player integration.
        
        Returns:
            list: List of device information dictionaries with composite IDs (alexa:serial)
        """
        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                logger.info(f"Discovering devices (attempt {attempt}/{self.retry_max_attempts})")
                
                # GraphQL query for smart home devices (from Home Assistant)
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
                                alexaDeviceIdentifierList
                            }
                        }
                    }
                }
                """
                
                # POST to GraphQL endpoint
                url = f"https://{self.domain}/nexus/v1/graphql"
                
                async with httpx.AsyncClient(cookies=self.cookies) as client:
                    response = await client.post(
                        url,
                        json={"query": query},
                        headers=self.headers,
                        timeout=self.max_timeout
                    )
                
                if response.status_code != 200:
                    logger.error(f"GraphQL API returned status {response.status_code}")
                    logger.error(f"Response: {response.text[:500]}")
                    
                    if attempt == self.retry_max_attempts:
                        return []
                    
                    # Retry with exponential backoff (async)
                    wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Parse JSON response
                try:
                    logger.debug(f"Response status: {response.status_code}")
                    logger.debug(f"Response headers: {dict(response.headers)}")
                    logger.debug(f"Response text length: {len(response.text)}")
                    logger.debug(f"Response text preview: {response.text[:200]}")
                    
                    data = response.json()
                    logger.debug(f"Parsed data type: {type(data)}")
                    logger.debug(f"Parsed data: {str(data)[:500]}")
                    
                    if data is None:
                        logger.error("API returned null response")
                        logger.error(f"Full response text: {response.text}")
                        
                        if attempt == self.retry_max_attempts:
                            return []
                        
                        wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                        logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                        
                except Exception as json_err:
                    logger.error(f"Failed to parse JSON response: {json_err}")
                    logger.debug(f"Response text: {response.text[:500]}")
                    
                    if attempt == self.retry_max_attempts:
                        return []
                    
                    wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                endpoints = data.get('data', {}).get('endpoints', {}).get('items', [])
                
                if not endpoints:
                    logger.warning("No endpoints found in GraphQL response")
                    return []
                
                air_quality_monitors = []
                
                # Find Air Quality Monitors
                for endpoint in endpoints:
                    appliance = endpoint.get('legacyAppliance', {})
                    if not appliance:
                        continue
                    
                    friendly_desc = appliance.get('friendlyDescription', '')
                    appliance_types = appliance.get('applianceTypes', [])
                    
                    # Check if this is an Air Quality Monitor
                    if (friendly_desc == "Amazon Indoor Air Quality Monitor" and
                        "AIR_QUALITY_MONITOR" in appliance_types):
                        
                        # Extract device serial
                        device_serial = None
                        alexa_device_ids = appliance.get('alexaDeviceIdentifierList', [])
                        for device_id in alexa_device_ids:
                            if isinstance(device_id, dict):
                                serial = device_id.get('dmsDeviceSerialNumber')
                                if serial:
                                    device_serial = serial
                                    break
                        
                        if not device_serial:
                            logger.warning(f"No serial found for device: {appliance.get('friendlyName')}")
                            continue
                        
                        device_info = {
                            'device_id': f'alexa:{device_serial}',  # Composite ID format
                            'entity_id': appliance.get('entityId'),
                            'appliance_id': appliance.get('applianceId'),
                            'friendly_name': appliance.get('friendlyName'),
                            'device_serial': device_serial,
                            'capabilities': appliance.get('capabilities', []),
                        }
                        
                        air_quality_monitors.append(device_info)
                        logger.info(f"Found Air Quality Monitor: {device_info['friendly_name']} ({device_info['device_id']})")
                
                return air_quality_monitors
                
            except Exception as e:
                logger.error(f"Error discovering devices (attempt {attempt}): {e}", exc_info=True)
                
                if attempt == self.retry_max_attempts:
                    return []
                
                # Retry with exponential backoff (async)
                wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        return []
    
    async def get_air_quality_readings(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current air quality readings for a device from phoenix state API.
        
        Uses the CORRECT endpoint structure discovered from alexapy v1.29.5:
        - POST to /api/phoenix/state (not GET)
        - entityType: "ENTITY" (not "APPLIANCE")
        - Returns capabilityStates as JSON strings
        
        Args:
            entity_id: Entity ID from device discovery
            
        Returns:
            dict: Readings including temperature, humidity, PM2.5, VOC, CO, IAQ, or None if failed
        """
        import json  # For parsing capabilityStates JSON strings
        
        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                logger.info(f"Fetching readings (attempt {attempt}/{self.retry_max_attempts})")
                
                # CORRECT endpoint structure (from working v5.0.5)
                url = f"https://{self.domain}/api/phoenix/state"
                payload = {
                    "stateRequests": [{
                        "entityId": entity_id,
                        "entityType": "ENTITY"  # CRITICAL: "ENTITY" not "APPLIANCE"
                    }]
                }
                
                # POST request (not GET!) using async httpx
                async with httpx.AsyncClient(cookies=self.cookies) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=self.headers,
                        timeout=self.max_timeout
                    )
                
                if response.status_code != 200:
                    logger.error(f"State API returned status {response.status_code}")
                    
                    if attempt == self.retry_max_attempts:
                        return None
                    
                    wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                data = response.json()
                device_states = data.get("deviceStates", [])
                
                if not device_states:
                    logger.warning(f"No device states found for entity {entity_id}")
                    return None
                
                # Get first device state
                device_state = device_states[0]
                cap_states_json = device_state.get("capabilityStates", [])
                
                if not cap_states_json:
                    logger.warning(f"No capability states found for entity {entity_id}")
                    return None
                
                # Parse capability states (they're JSON strings!)
                readings = {
                    'timestamp': datetime.now().isoformat(),
                }
                
                # Instance ID mapping (from GraphQL discovery and v5.0.5 code)
                # Based on research from Sprint 2, these are the known sensor mappings
                instance_mapping = {
                    "4": "humidity_percent",
                    "5": "voc_ppb",
                    "6": "pm25_ugm3",
                    "7": "unknown_7",  # TODO: Unknown sensor - appears in API but purpose unclear. Stored for future analysis.
                    "8": "co_ppm",
                    "9": "iaq_score",  # Indoor Air Quality score
                }
                
                for cap_state_json in cap_states_json:
                    cap_state = json.loads(cap_state_json)
                    namespace = cap_state.get("namespace", "")
                    name = cap_state.get("name", "")
                    value = cap_state.get("value")
                    instance = str(cap_state.get("instance", ""))
                    
                    # Temperature sensor
                    if namespace == "Alexa.TemperatureSensor" and name == "temperature":
                        if isinstance(value, dict):
                            temp_value = value.get("value")
                            temp_scale = value.get("scale", "CELSIUS")
                            
                            if temp_scale == "CELSIUS":
                                readings["temperature_celsius"] = float(temp_value)
                            elif temp_scale == "FAHRENHEIT":
                                # Convert to Celsius
                                readings["temperature_celsius"] = (float(temp_value) - 32) * 5 / 9
                    
                    # RangeController values (air quality sensors)
                    elif namespace == "Alexa.RangeController" and name == "rangeValue":
                        if instance in instance_mapping:
                            field_name = instance_mapping[instance]
                            readings[field_name] = float(value)
                            logger.debug(f"  Instance {instance} ({field_name}): {value}")
                    
                    # Endpoint health
                    elif namespace == "Alexa.EndpointHealth" and name == "connectivity":
                        if isinstance(value, dict):
                            readings["connectivity"] = value.get("value")
                
                logger.info(f"Collected {len(readings) - 1} readings from entity {entity_id}")
                return readings
                
            except Exception as e:
                logger.error(f"Error fetching readings (attempt {attempt}): {e}", exc_info=True)
                
                if attempt == self.retry_max_attempts:
                    return None
                
                wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        return None
    
    def validate_readings(self, readings: Dict[str, Any]) -> List[str]:
        """
        Validate air quality readings against acceptable ranges.
        
        Args:
            readings: Dictionary of sensor readings
            
        Returns:
            list: List of validation errors (empty if all valid)
        """
        errors = []
        
        # Temperature validation (0-40°C per constitution)
        if 'temperature_celsius' in readings:
            temp = readings['temperature_celsius']
            if not (0 <= temp <= 40):
                errors.append(f"Temperature out of range: {temp}°C (expected 0-40°C)")
        
        # Humidity validation (0-100%)
        if 'humidity_percent' in readings:
            humidity = readings['humidity_percent']
            if not (0 <= humidity <= 100):
                errors.append(f"Humidity out of range: {humidity}% (expected 0-100%)")
        
        # PM2.5 validation (non-negative)
        if 'pm25_ugm3' in readings:
            pm25 = readings['pm25_ugm3']
            if pm25 < 0:
                errors.append(f"PM2.5 cannot be negative: {pm25} µg/m³")
        
        # VOC validation (non-negative)
        if 'voc_ppb' in readings:
            voc = readings['voc_ppb']
            if voc < 0:
                errors.append(f"VOC cannot be negative: {voc} ppb")
        
        # CO validation (non-negative) - Carbon Monoxide in ppm
        if 'co_ppm' in readings:
            co = readings['co_ppm']
            if co < 0:
                errors.append(f"CO cannot be negative: {co} ppm")
        
        # IAQ score validation (0-100 scale)
        if 'iaq_score' in readings:
            iaq = readings['iaq_score']
            if not (0 <= iaq <= 100):
                errors.append(f"IAQ score out of range: {iaq} (expected 0-100)")
        
        return errors
    
    def format_reading_for_db(self, entity_id: str, serial: str, readings: dict, config: dict) -> dict:
        """
        Format AQM readings for database insertion.
        
        Args:
            entity_id: Device entity ID
            serial: Device serial number
            readings: Raw readings from get_air_quality_readings()
            config: Configuration dict
            
        Returns:
            dict: Formatted reading ready for database
        """
        # Get location from config mapping (e.g., "GAJ123..." -> "Living Room")
        # Falls back to 'Unknown' if device not in mapping
        locations = config.get('amazon_aqm', {}).get('device_locations', {})
        location = locations.get(serial, config.get('amazon_aqm', {}).get('fallback_location', 'Unknown'))
        
        # Build device_id in standard format: alexa:serial
        # This distinguishes AQM devices from Hue sensors (hue:id)
        device_id = f"alexa:{serial}"
        
        # Format reading with all sensor fields
        # All air quality fields are optional (some devices lack certain sensors)
        db_reading = {
            'timestamp': readings['timestamp'],
            'device_id': device_id,
            'temperature_celsius': readings.get('temperature_celsius'),  # Required
            'location': location,
            'device_type': 'alexa_aqm',
            'humidity_percent': readings.get('humidity_percent'),  # Optional
            'pm25_ugm3': readings.get('pm25_ugm3'),  # Particulate matter (optional)
            'voc_ppb': readings.get('voc_ppb'),  # Volatile organic compounds (optional)
            'co_ppm': readings.get('co_ppm'),  # Carbon monoxide (optional)
            'iaq_score': readings.get('iaq_score'),  # Indoor air quality index (optional)
        }
        
        # Optionally include raw API response for debugging/auditing
        # Disabled by default to save database space
        if config.get('amazon_aqm', {}).get('collect_raw_response', False):
            import json
            db_reading['raw_response'] = json.dumps(readings)
        
        return db_reading
    
    async def collect_and_store(self, db_manager) -> bool:
        """
        Convenience function to collect AQM data and store in database.
        Handles full workflow: discovery → collection → validation → storage
        
        Args:
            db_manager: DatabaseManager instance
            
        Returns:
            bool: True if at least one reading was stored successfully, False otherwise
        """
        try:
            # Step 1: Discover all AQM devices registered to this account
            devices = await self.list_devices()
            
            if not devices:
                logger.warning("No Amazon Air Quality Monitors found")
                return False
            
            # Step 2: Collect from each device
            success_count = 0
            for device in devices:
                entity_id = device['entity_id']
                serial = device['device_serial']
                
                # Step 3: Get readings from Phoenix State API
                readings = await self.get_air_quality_readings(entity_id)
                
                if not readings:
                    logger.error(f"Failed to get readings from {serial}")
                    continue
                
                # Step 4: Validate readings (temp range, non-negative values, etc.)
                # Validation failures logged but don't block storage
                errors = self.validate_readings(readings)
                if errors:
                    logger.warning(f"Validation errors for {serial}: {errors}")
                    # Continue anyway - store what we have
                
                # Step 5: Format for database insertion (add location, device_id, etc.)
                db_reading = self.format_reading_for_db(entity_id, serial, readings, self.config)
                
                # Step 6: Insert to database (UNIQUE constraint prevents duplicates)
                if db_manager.insert_temperature_reading(db_reading):
                    logger.info(f"Stored reading from {serial} ({device.get('friendly_name', 'Unknown')})")
                    success_count += 1
                else:
                    # Duplicate timestamp - expected behavior, not an error
                    logger.debug(f"Duplicate reading from {serial}, skipped")
            
            # Return True if at least one device was successfully stored
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error collecting AQM data: {e}", exc_info=True)
            return False


async def collect_amazon_aqm_data(cookies: Dict[str, str], config: dict = {}) -> Optional[Dict[str, Any]]:
    """
    Convenience function to collect air quality data from Amazon device.
    
    Args:
        cookies: Amazon authentication cookies (captured via Playwright)
        config: Configuration dictionary
        
    Returns:
        dict: Device info and readings, or None if failed
    """
    collector = AmazonAQMCollector(cookies, config)
    
    # Discover devices
    devices = await collector.list_devices()
    
    if not devices:
        logger.warning("No Amazon Air Quality Monitors found")
        return None
    
    # Use first device or find by serial if configured
    device = devices[0]
    device_serial = config.get('amazon_aqm', {}).get('device_serial')
    if device_serial:
        for d in devices:
            if d['device_serial'] == device_serial:
                device = d
                break
    
    logger.info(f"Collecting data from: {device['friendly_name']}")
    
    # Get readings
    readings = await collector.get_air_quality_readings(device['entity_id'])
    
    if not readings:
        return None
    
    # Validate
    errors = collector.validate_readings(readings)
    if errors:
        logger.warning(f"Validation errors: {errors}")
    
    return {
        'device_id': device['device_id'],
        'device_name': device['friendly_name'],
        'device_serial': device['device_serial'],
        'readings': readings,
        'validation_errors': errors,
    }
