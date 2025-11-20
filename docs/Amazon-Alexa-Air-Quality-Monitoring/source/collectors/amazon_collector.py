import logging
import requests
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class AmazonAQMCollector:
    """
    Collector for Amazon Smart Air Quality Monitor.
    Uses direct API calls with cookie authentication.
    Based on Home Assistant's Alexa Media Player integration patterns.
    """
    
    def __init__(self, config: Dict[str, Any], secrets: Dict[str, Any]):
        self.config = config
        self.secrets = secrets
        self.cookies = secrets.get('amazon_aqm', {}).get('cookies', {})
        self.domain = config.get('amazon_aqm', {}).get('domain', 'alexa.amazon.com')
        self.device_serial = config.get('amazon_aqm', {}).get('device_serial')
        
        # Extract CSRF token from cookies (required for API calls)
        self.csrf_token = self.cookies.get('csrf', '')
        
        # Set up session with cookies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://{self.domain}/spa/index.html',  # Required by Amazon
            'csrf': self.csrf_token,  # CSRF token from cookies
        })
        
        # Add cookies to session
        for name, value in self.cookies.items():
            self.session.cookies.set(name, value, domain='.amazon.com')

    def discover_devices(self) -> List[Dict[str, Any]]:
        """
        Discovers Amazon Air Quality Monitors via the GraphQL API.
        Returns list of device information dictionaries.
        """
        try:
            # GraphQL query (same as alexapy uses)
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
                            connectedVia
                            modelName
                            entityId
                            aliases
                            capabilities
                            customerDefinedDeviceType
                            alexaDeviceIdentifierList
                            driverIdentity
                        }
                    }
                }
            }
            """
            
            # Use the GraphQL endpoint
            url = f"https://{self.domain}/nexus/v1/graphql"
            response = self.session.post(url, json={"query": query}, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"GraphQL API returned status {response.status_code}")
                logger.debug(f"Response: {response.text[:500]}")
                return []
            
            data = response.json()
            
            # Parse GraphQL response
            endpoints = data.get('data', {}).get('endpoints', {}).get('items', [])
            
            if not endpoints:
                logger.warning("No endpoints found in GraphQL response")
                return []
            
            air_quality_monitors = []
            
            # Parse endpoints to find Air Quality Monitors
            for endpoint in endpoints:
                appliance = endpoint.get('legacyAppliance', {})
                if not appliance:
                    continue
                
                friendly_desc = appliance.get('friendlyDescription', '')
                appliance_types = appliance.get('applianceTypes', [])
                
                # Check if this is an Air Quality Monitor
                # Based on Home Assistant's is_air_quality_sensor() function
                if (friendly_desc == "Amazon Indoor Air Quality Monitor" and
                    "AIR_QUALITY_MONITOR" in appliance_types):
                    
                    device_info = {
                        'entity_id': appliance.get('entityId'),
                        'appliance_id': appliance.get('applianceId'),
                        'friendly_name': appliance.get('friendlyName'),
                        'capabilities': appliance.get('capabilities', []),
                    }
                    
                    # Extract device serial if available
                    alexa_device_ids = appliance.get('alexaDeviceIdentifierList', [])
                    for device_id in alexa_device_ids:
                        if isinstance(device_id, dict):
                            serial = device_id.get('dmsDeviceSerialNumber')
                            if serial:
                                device_info['device_serial'] = serial
                                break
                    
                    # Parse sensor capabilities
                    device_info['sensors'] = self._parse_sensors(appliance.get('capabilities', []))
                    
                    air_quality_monitors.append(device_info)
                    logger.info(f"Found Air Quality Monitor: {device_info['friendly_name']}")
            
            return air_quality_monitors
            
        except Exception as e:
            logger.error(f"Error discovering devices: {e}", exc_info=True)
            return []

    def _parse_sensors(self, capabilities: List[Dict]) -> List[Dict[str, str]]:
        """
        Parse capabilities to extract sensor information.
        Based on Home Assistant's capability parsing logic.
        """
        sensors = []
        
        for cap in capabilities:
            instance = cap.get('instance')
            if not instance:
                continue
            
            # Get friendly names to identify sensor type
            friendly_names = cap.get('resources', {}).get('friendlyNames', [])
            for name_entry in friendly_names:
                asset_id = name_entry.get('value', {}).get('assetId', '')
                
                # Check if this is an air quality sensor
                if asset_id and asset_id.startswith('Alexa.AirQuality'):
                    unit = cap.get('configuration', {}).get('unitOfMeasure', '')
                    sensor = {
                        'type': asset_id,
                        'instance': instance,
                        'unit': unit,
                        'name': asset_id.replace('Alexa.AirQuality.', '')
                    }
                    sensors.append(sensor)
        
        return sensors

    def get_air_quality_data(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches current air quality data for a specific device.
        Uses the phoenix state API endpoint.
        """
        try:
            # Get entity state data
            url = f"https://{self.domain}/api/phoenix/state"
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"State API returned status {response.status_code}")
                return None
            
            # The response should contain capability states for all entities
            data = response.json()
            
            # Find our entity's data
            entity_data = data.get(entity_id, [])
            
            if not entity_data:
                logger.warning(f"No state data found for entity {entity_id}")
                return None
            
            # Parse the capability states
            parsed_data = {}
            
            for state in entity_data:
                namespace = state.get('namespace', '')
                name = state.get('name', '')
                value = state.get('value')
                
                # Temperature sensor
                if namespace == 'Alexa.TemperatureSensor' and name == 'temperature':
                    if isinstance(value, dict):
                        parsed_data['temperature'] = {
                            'value': value.get('value'),
                            'unit': value.get('scale', 'CELSIUS')
                        }
                
                # Range controller (used for air quality sensors)
                elif namespace == 'Alexa.RangeController' and name == 'rangeValue':
                    # We need to match this with the sensor instance
                    # For now, store it generically
                    instance = state.get('instance', 'unknown')
                    parsed_data[f'sensor_{instance}'] = {
                        'value': value,
                        'instance': instance
                    }
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error fetching air quality data: {e}", exc_info=True)
            return None

    def collect(self) -> Dict[str, Any]:
        """
        Main collection method.
        Discovers devices and collects current air quality data.
        """
        if not self.cookies:
            logger.error("No Amazon cookies provided.")
            return {}

        try:
            # Discover devices
            devices = self.discover_devices()
            
            if not devices:
                logger.warning("No Amazon Air Quality Monitor found.")
                return {}
            
            # Use the first device (or find by serial if configured)
            device = devices[0]
            if self.device_serial:
                for d in devices:
                    if d.get('device_serial') == self.device_serial:
                        device = d
                        break
            
            logger.info(f"Collecting data from: {device['friendly_name']}")
            
            # Get current air quality data
            data = self.get_air_quality_data(device['entity_id'])
            
            if data:
                # Add device metadata
                result = {
                    'device_name': device['friendly_name'],
                    'device_serial': device.get('device_serial', 'unknown'),
                    'sensors': device.get('sensors', []),
                    'readings': data
                }
                logger.info(f"Successfully collected data with {len(data)} readings")
                return result
            else:
                logger.warning("No data returned from device")
                return {}
                
        except Exception as e:
            logger.error(f"Error in collect: {e}", exc_info=True)
            return {}
