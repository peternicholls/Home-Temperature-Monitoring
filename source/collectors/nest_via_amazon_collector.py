#!/usr/bin/env python3
"""
Nest Thermostat via Amazon Alexa Collector

Collects temperature and mode data from Nest thermostats through Alexa's Phoenix State API.
Uses cookie-based authentication (same as Amazon AQM collector).

Based on research from docs/amazon-nest-findings.md
Tested with Nest Learning Thermostat (Hallway device).
"""

import httpx
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path

from source.utils.structured_logger import StructuredLogger


class NestViaAmazonCollector:
    """
    Collector for Nest thermostats via Amazon Alexa.
    
    Features:
    - GraphQL API for device discovery
    - Cookie-based authentication
    - Temperature and mode readings
    - Retry logic with exponential backoff
    - Direct HTTP requests to Alexa APIs
    """
    
    def __init__(self, cookies: Dict[str, str], config: dict = {}, logger: Optional[StructuredLogger] = None):
        """
        Initialize collector with Amazon cookies.
        
        Args:
            cookies: Dictionary of Amazon cookies from authentication
            config: Configuration dictionary with retry settings
            logger: Optional StructuredLogger instance for logging
        """
        self.cookies = cookies
        self.config = config or {}
        self.logger = logger or StructuredLogger(config) if config else None
        
        # Extract configuration
        collection_config = self.config.get('collection', {})
        self.retry_max_attempts = collection_config.get('retry_attempts', 5)
        self.retry_base_delay = collection_config.get('retry_backoff_base', 1.0)
        self.max_timeout = collection_config.get('max_timeout', 120)
        
        # Amazon API configuration
        amazon_config = config.get('collectors', {}).get('amazon_aqm', {})
        self.domain = amazon_config.get('domain', 'alexa.amazon.co.uk')
        
        if self.logger:
            self.logger.debug(f"Configured domain: {self.domain}")
        
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
        
        self.cookies = cookies
        if self.logger:
            self.logger.debug(f"Configured {len(cookies)} cookies for domain: {self.domain}")
    
    async def list_devices(self) -> List[Dict[str, Any]]:
        """
        Discover Nest thermostats via GraphQL API.
        
        Returns:
            list: List of device information dictionaries with device IDs
        """
        data = None
        
        # Try to fetch and parse data with retries
        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                if self.logger:
                    self.logger.info(f"Discovering Nest devices (attempt {attempt}/{self.retry_max_attempts})")
                
                # GraphQL query for smart home devices
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
                    if self.logger:
                        self.logger.error(f"GraphQL API returned status {response.status_code}")
                    if self.logger:
                        self.logger.debug(f"Response text: {response.text[:500]}")
                    
                    if attempt == self.retry_max_attempts:
                        return []
                    
                    wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                    if self.logger:
                        self.logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Parse JSON response
                data = response.json()
                if self.logger:
                    self.logger.debug(f"Response type: {type(data)}")
                
                if not isinstance(data, dict) or data is None:
                    if self.logger:
                        self.logger.error("Invalid response: expected dict")
                    if attempt == self.retry_max_attempts:
                        return []
                    wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(wait_time)
                    continue
                
                # Successfully got data - exit retry loop
                break
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error fetching devices (attempt {attempt}): {e}", exc_info=True)
                
                if attempt == self.retry_max_attempts:
                    return []
                
                wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                if self.logger:
                    self.logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        # If we don't have data at this point, return empty
        if data is None:
            if self.logger:
                self.logger.error("No data received from GraphQL API")
            return []
        
        # Process endpoints (outside retry loop)
        try:
            endpoints = data.get('data', {}).get('endpoints', {}).get('items', [])
            
            if not endpoints:
                if self.logger:
                    self.logger.warning("No endpoints found in GraphQL response")
                return []
            
            nest_devices = []
            if self.logger:
                self.logger.debug(f"Processing {len(endpoints)} endpoints")
            
            # Find Nest thermostats
            for endpoint in endpoints:
                appliance = endpoint.get('legacyAppliance', {})
                if not appliance:
                    continue
                
                manufacturer = appliance.get('manufacturerName', '')
                appliance_types = appliance.get('applianceTypes', [])
                friendly_name = appliance.get('friendlyName', 'Unknown')
                
                if self.logger:
                    self.logger.debug(f"Device: {friendly_name} | Mfg: {manufacturer} | Types: {appliance_types}")
                
                # Check if this is a Nest thermostat
                if 'Nest' in manufacturer and 'THERMOSTAT' in appliance_types:
                    
                    device_info = {
                        'device_id': f'nest:{appliance.get("applianceId", "")}',
                        'appliance_id': appliance.get('applianceId'),
                        'friendly_name': appliance.get('friendlyName'),
                        'manufacturer': manufacturer,
                        'model_name': appliance.get('modelName'),
                        'capabilities': appliance.get('capabilities', []),
                    }
                    
                    nest_devices.append(device_info)
                    if self.logger:
                        self.logger.info(f"Found Nest thermostat: {device_info['friendly_name']} ({device_info['device_id']})")
            
            return nest_devices
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error processing endpoints: {e}", exc_info=True)
            return []
    
    async def get_thermostat_readings(self, appliance_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current temperature and mode from Nest thermostat via Phoenix State API.
        
        Args:
            appliance_id: Appliance ID from device discovery (SKILL_... format)
            
        Returns:
            dict: Readings including temperature_celsius and thermostat_mode, or None if failed
        """
        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                if self.logger:
                    self.logger.info(f"Fetching thermostat readings (attempt {attempt}/{self.retry_max_attempts})")
                
                # Phoenix State API endpoint
                url = f"https://{self.domain}/api/phoenix/state"
                payload = {
                    "stateRequests": [{
                        "entityId": appliance_id,
                        "entityType": "APPLIANCE"
                    }]
                }
                
                # POST request using async httpx
                async with httpx.AsyncClient(cookies=self.cookies) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=self.headers,
                        timeout=self.max_timeout
                    )
                
                if response.status_code != 200:
                    if self.logger:
                        self.logger.error(f"State API returned status {response.status_code}")
                    
                    # Permanent auth error (401/403): create alert file
                    if response.status_code in (401, 403):
                        if self.logger:
                            self.logger.critical(f"Permanent auth error {response.status_code}: token refresh needed")
                        
                        alert_file = Path('data/ALERT_TOKEN_REFRESH_NEEDED.txt')
                        try:
                            alert_file.parent.mkdir(parents=True, exist_ok=True)
                            alert_file.write_text("Amazon Alexa token refresh required. Please re-authenticate.")
                            if self.logger:
                                self.logger.info(f"Alert file created: {alert_file}")
                        except Exception as file_err:
                            if self.logger:
                                self.logger.error(f"Failed to create alert file: {file_err}")
                    
                    if attempt == self.retry_max_attempts:
                        return None
                    
                    wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                    if self.logger:
                        self.logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                data = response.json()
                device_states = data.get("deviceStates", [])
                
                if not device_states:
                    if self.logger:
                        self.logger.warning(f"No device states found for appliance {appliance_id}")
                    return None
                
                # Get first device state
                device_state = device_states[0]
                cap_states_json = device_state.get("capabilityStates", [])
                
                if not cap_states_json:
                    if self.logger:
                        self.logger.warning(f"No capability states found for appliance {appliance_id}")
                    return None
                
                # Parse capability states (they're JSON strings!)
                readings: Dict[str, Any] = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                }
                
                for cap_state_json in cap_states_json:
                    cap_state = json.loads(cap_state_json)
                    namespace = cap_state.get("namespace", "")
                    name = cap_state.get("name", "")
                    value = cap_state.get("value")
                    
                    # Temperature sensor (Celsius)
                    if namespace == "Alexa.TemperatureSensor" and name == "temperature":
                        if isinstance(value, dict):
                            temp_value = value.get("value")
                            temp_scale = value.get("scale", "CELSIUS")
                            
                            if temp_value is not None:
                                if temp_scale == "CELSIUS":
                                    readings["temperature_celsius"] = float(temp_value)
                                elif temp_scale == "FAHRENHEIT":
                                    # Convert to Celsius
                                    readings["temperature_celsius"] = (float(temp_value) - 32) * 5 / 9
                    
                    # No longer storing thermostat_mode as it does not reflect actual heating/cooling state
                    
                    # Connectivity health
                    elif namespace == "Alexa.EndpointHealth" and name == "connectivity":
                        if isinstance(value, dict):
                            connectivity = value.get("value")
                            if connectivity is not None:
                                readings["connectivity"] = str(connectivity)
                
                if "temperature_celsius" not in readings:
                    if self.logger:
                        self.logger.warning("No temperature reading found in capability states")
                    return None
                
                if self.logger:
                    self.logger.info(f"Collected readings from Nest thermostat")
                if self.logger:
                    self.logger.debug(f"  Temperature: {readings.get('temperature_celsius')}°C")
                if self.logger:
                    self.logger.debug(f"  Connectivity: {readings.get('connectivity')}")
                
                # Success: auto-clear alert file if it exists
                alert_file = Path('data/ALERT_TOKEN_REFRESH_NEEDED.txt')
                if alert_file.exists():
                    try:
                        alert_file.unlink()
                        if self.logger:
                            self.logger.info(f"Alert file cleared: {alert_file}")
                    except Exception as file_err:
                        if self.logger:
                            self.logger.error(f"Failed to clear alert file: {file_err}")
                
                return readings
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error fetching readings (attempt {attempt}): {e}", exc_info=True)
                
                if attempt == self.retry_max_attempts:
                    return None
                
                wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                if self.logger:
                    self.logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        return None
    
    def validate_readings(self, readings: Dict[str, Any]) -> List[str]:
        """
        Validate thermostat readings against acceptable ranges.
        
        Args:
            readings: Dictionary of sensor readings
            
        Returns:
            list: List of validation errors (empty if all valid)
        """
        errors = []
        
        # Temperature validation (reasonable range for indoors)
        if 'temperature_celsius' in readings:
            temp = readings['temperature_celsius']
            if not (0 <= temp <= 40):
                errors.append(f"Temperature out of range: {temp}°C (expected 0-40°C)")
        
        # No mode validation; thermostat_mode is not stored
        
        return errors
    
    def format_reading_for_db(self, device_id: str, friendly_name: str, readings: dict, config: dict) -> dict:
        """
        Format thermostat readings for database insertion.
        
        Args:
            device_id: Device identifier (nest:appliance_id)
            friendly_name: Human-readable device name
            readings: Raw readings from get_thermostat_readings()
            config: Configuration dict
            
        Returns:
            dict: Formatted reading ready for database
        """
        # Get location from config mapping or use friendly name
        locations = config.get('amazon_aqm', {}).get('device_locations', {})
        location = locations.get(device_id, friendly_name)
        
        # Infer device name from location + type
        from source.storage.yaml_device_registry import infer_device_name
        device_name = infer_device_name(location, 'nest_thermostat', device_id)
        
        # Format reading with all thermostat fields
        db_reading = {
            'timestamp': readings['timestamp'],
            'device_id': device_id,
            'temperature_celsius': readings.get('temperature_celsius'),  # Required
            'location': location,
            'name': device_name,  # Use inferred name (location + type)
            'device_type': 'nest_thermostat',
        }
        
        # Optionally include raw API response for debugging
        if config.get('amazon_aqm', {}).get('collect_raw_response', False):
            db_reading['raw_response'] = json.dumps(readings)
        
        return db_reading
    
    async def collect_and_store(self, db_manager) -> bool:
        """
        Convenience function to collect Nest data and store in database.
        Handles full workflow: discovery → collection → validation → storage
        
        Args:
            db_manager: DatabaseManager instance
            
        Returns:
            bool: True if at least one reading was stored successfully, False otherwise
        """
        try:
            # Step 1: Discover all Nest thermostats registered to this account
            devices = await self.list_devices()
            
            if not devices:
                if self.logger:
                    self.logger.warning("No Nest thermostats found")
                return False
            
            # Step 2: Collect from each device
            success_count = 0
            for device in devices:
                appliance_id = device['appliance_id']
                device_id = device['device_id']
                friendly_name = device['friendly_name']
                
                # Step 3: Get readings from Phoenix State API
                readings = await self.get_thermostat_readings(appliance_id)
                
                if not readings:
                    if self.logger:
                        self.logger.error(f"Failed to get readings from {friendly_name}")
                    continue
                
                # Step 4: Validate readings
                errors = self.validate_readings(readings)
                if errors:
                    if self.logger:
                        self.logger.warning(f"Validation errors for {friendly_name}: {errors}")
                    # Continue anyway - store what we have
                
                # Step 5: Format for database insertion
                db_reading = self.format_reading_for_db(device_id, friendly_name, readings, self.config)
                
                # Step 6: Insert to database
                if db_manager.insert_temperature_reading(db_reading):
                    if self.logger:
                        self.logger.info(f"Stored reading from {friendly_name} (temperature: {readings.get('temperature_celsius')}°C)")
                    success_count += 1
                else:
                    # Duplicate timestamp - expected behavior
                    if self.logger:
                        self.logger.debug(f"Duplicate reading from {friendly_name}, skipped")
            
            # Return True if at least one device was successfully stored
            return success_count > 0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error collecting Nest data: {e}", exc_info=True)
            return False


async def collect_nest_via_amazon(cookies: Dict[str, str], config: dict = {}, logger: Optional[StructuredLogger] = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to collect Nest thermostat data via Alexa.
    
    Args:
        cookies: Amazon authentication cookies
        config: Configuration dictionary
        logger: Optional StructuredLogger instance for logging
        
    Returns:
        dict: Device info and readings, or None if failed
    """
    collector = NestViaAmazonCollector(cookies, config, logger)
    
    # Discover devices
    devices = await collector.list_devices()
    
    if not devices:
        if logger:
            logger.warning("No Nest thermostats found")
        return None
    
    # Use first device
    device = devices[0]
    appliance_id = device['appliance_id']
    
    if logger:
        logger.info(f"Collecting data from: {device['friendly_name']}")
    
    # Get readings
    readings = await collector.get_thermostat_readings(appliance_id)
    
    if not readings:
        return None
    
    # Validate
    errors = collector.validate_readings(readings)
    if errors:
        if logger:
            logger.warning(f"Validation errors: {errors}")
    
    return {
        'device_id': device['device_id'],
        'device_name': device['friendly_name'],
        'readings': readings,
        'validation_errors': errors,
    }
