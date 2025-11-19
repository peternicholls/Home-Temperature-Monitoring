#!/usr/bin/env python3
"""
Philips Hue Temperature Collector

Discovers temperature sensors on Hue Bridge and collects temperature readings.
Stores data in SQLite database with proper formatting and validation.

Usage:
    # Discover sensors
    python source/collectors/hue_collector.py --discover
    
    # Collect once
    python source/collectors/hue_collector.py --collect-once
    
    # Continuous collection (every 5 minutes)
    python source/collectors/hue_collector.py --continuous
"""

import argparse
import json
import logging
import sys
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Ensure project root is on sys.path so `import source.*` works when running as script
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
except Exception:
    pass

try:
    from phue import Bridge
    import requests
except ImportError:
    print("ERROR: Required package 'phue' not installed")
    print("Run: pip install phue")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)


def load_secrets(secrets_path: str = "config/secrets.yaml") -> dict:
    """Load secrets from YAML file."""
    try:
        with open(secrets_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load secrets: {e}")
        logger.error("Have you run authentication? Run: python source/collectors/hue_auth.py")
        sys.exit(1)


def connect_to_bridge(config: dict, secrets: dict) -> Bridge:
    """
    Connect to Hue Bridge using stored credentials.
    
    Args:
        config: Configuration dictionary
        secrets: Secrets dictionary with API key
        
    Returns:
        Bridge: Connected Bridge object
    """
    hue_config = config.get('collectors', {}).get('hue', {})
    hue_secrets = secrets.get('hue', {})
    
    bridge_ip = hue_config.get('bridge_ip')
    api_key = hue_secrets.get('api_key')
    
    if not api_key:
        logger.error("No API key found in secrets.yaml")
        logger.error("Run authentication first: python source/collectors/hue_auth.py")
        sys.exit(1)
    
    # Auto-discover if no IP configured
    if not bridge_ip:
        logger.info("No bridge_ip in config, using stored credentials...")
        # phue will use the stored IP from previous connection
        bridge = Bridge(ip=None, username=api_key)
    else:
        bridge = Bridge(ip=bridge_ip, username=api_key)
    
    try:
        # Test connection
        bridge.get_api()
        logger.info("Successfully connected to Hue Bridge")
        return bridge
    except Exception as e:
        logger.error(f"Failed to connect to Bridge: {e}")
        sys.exit(1)


def get_sensor_location(sensor_data: dict, config: dict) -> str:
    """
    Map sensor to location using config or fallback to sensor name.
    
    Args:
        sensor_data: Sensor data from Hue API
        config: Configuration dictionary
        
    Returns:
        str: Location name
    """
    hue_config = config.get('collectors', {}).get('hue', {})
    # Coalesce None to empty dict if sensor_locations is explicitly set to null in YAML
    sensor_locations = hue_config.get('sensor_locations') or {}
    fallback_to_name = hue_config.get('fallback_to_name', True)
    
    unique_id = sensor_data.get('uniqueid', '')
    
    # Try to find in config mapping
    if unique_id in sensor_locations:
        return sensor_locations[unique_id]
    
    # Fallback to sensor name
    if fallback_to_name:
        return sensor_data.get('name', 'Unknown')
    
    return unique_id


def discover_sensors(bridge: Bridge, config: dict) -> List[Dict]:
    """
    Discover all temperature-capable Hue sensors.
    
    Args:
        bridge: Connected Bridge object
        config: Configuration dictionary
        
    Returns:
        List of sensor dictionaries with metadata
    """
    logger.info("Discovering temperature sensors...")
    
    try:
        # Optimized: Use sensors-only endpoint instead of full config
        # This reduces payload size by 50%+ and speeds up collection
        import sys
        api_key = None
        bridge_ip = None
        
        # Extract API key and IP from bridge object
        if hasattr(bridge, 'username'):
            api_key = bridge.username
        if hasattr(bridge, 'ip'):
            bridge_ip = bridge.ip
        
        if api_key and bridge_ip:
            # Direct API call to sensors endpoint (optimized)
            response = requests.get(f"http://{bridge_ip}/api/{api_key}/sensors", timeout=10)
            response.raise_for_status()
            all_sensors = response.json()
            
            # Log performance metrics
            response_size = sys.getsizeof(response.text)
            logger.info(f"API request metrics: sensors_only endpoint, {response_size} bytes")
        else:
            # Fallback to full config if optimization not possible
            logger.debug("Using fallback full config API call")
            api_data = bridge.get_api()
            all_sensors = api_data.get('sensors', {})
            
    except Exception as e:
        logger.warning(f"Optimized API call failed, falling back to full config: {e}")
        # Fallback to original method
        api_data = bridge.get_api()
        all_sensors = api_data.get('sensors', {})
    
    temperature_sensors = []
    
    for sensor_id, sensor_data in all_sensors.items():
        # Filter for temperature sensors only
        if sensor_data.get('type') != 'ZLLTemperature':
            continue
        
        sensor_info = {
            'sensor_id': sensor_id,
            'unique_id': sensor_data.get('uniqueid', ''),
            'name': sensor_data.get('name', 'Unknown'),
            'model_id': sensor_data.get('modelid', ''),
            'manufacturer': sensor_data.get('manufacturername', ''),
            'sensor_type': sensor_data.get('type', ''),
            'location': get_sensor_location(sensor_data, config),
            'is_reachable': sensor_data.get('config', {}).get('reachable', False),
            'battery_level': sensor_data.get('config', {}).get('battery'),
            'last_updated': sensor_data.get('state', {}).get('lastupdated'),
        }
        
        temperature_sensors.append(sensor_info)
        
        status = "✓ Online" if sensor_info['is_reachable'] else "✗ Offline"
        battery = f"{sensor_info['battery_level']}%" if sensor_info['battery_level'] else "N/A"
        logger.info(f"  [{status}] {sensor_info['location']} - Battery: {battery}")
    
    logger.info(f"Found {len(temperature_sensors)} temperature sensor(s)")
    return temperature_sensors


def convert_temperature(raw_temp: int) -> float:
    """
    Convert temperature from 0.01°C units to Celsius.
    
    Args:
        raw_temp: Temperature in 0.01°C units (e.g., 2134 = 21.34°C)
        
    Returns:
        float: Temperature in Celsius
    """
    return raw_temp / 100.0


def is_temperature_anomalous(temp_celsius: float, config: dict) -> bool:
    """
    Check if temperature is outside valid indoor range.
    
    Args:
        temp_celsius: Temperature in Celsius
        config: Configuration dictionary
        
    Returns:
        bool: True if anomalous, False otherwise
    """
    hue_config = config.get('collectors', {}).get('hue', {})
    temp_min = hue_config.get('temperature_min', 0.0)
    temp_max = hue_config.get('temperature_max', 40.0)
    
    return temp_celsius < temp_min or temp_celsius > temp_max


def collect_reading_from_sensor(bridge: Bridge, sensor_id: str, sensor_info: dict, config: dict, cached_sensors_data: Optional[dict] = None) -> Optional[Dict]:
    """
    Collect a single temperature reading from a sensor.
    
    Args:
        bridge: Connected Bridge object
        sensor_id: Sensor ID to read from
        sensor_info: Sensor metadata dictionary
        config: Configuration dictionary
        cached_sensors_data: Pre-fetched sensors data to avoid redundant API calls
        
    Returns:
        Reading dictionary or None if sensor is offline/has no data
        
    Raises:
        requests.RequestException: For transient API/network errors (allows retry)
        Exception: For other errors (no retry)
    """
    try:
        # Use cached data if provided, otherwise fetch
        if cached_sensors_data is not None:
            sensor_data = cached_sensors_data.get(sensor_id)
            if not sensor_data:
                logger.warning(f"Sensor {sensor_info['location']} not found in cached data")
                return None
        else:
            # Fallback to per-sensor API call (less efficient)
            api_key = bridge.username if hasattr(bridge, 'username') else None
            bridge_ip = bridge.ip if hasattr(bridge, 'ip') else None
            
            if api_key and bridge_ip:
                # Direct API call to specific sensor endpoint
                start_time = time.time()
                response = requests.get(f"http://{bridge_ip}/api/{api_key}/sensors/{sensor_id}", timeout=10)
                response.raise_for_status()  # Raises for HTTP errors - allows retry
                sensor_data = response.json()
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Log API request metadata
                response_size = sys.getsizeof(response.text)
                logger.debug(f"API metrics: single sensor, {response_size} bytes, {duration_ms}ms")
            else:
                # Fallback to full config
                api_data = bridge.get_api()
                sensor_data = api_data['sensors'][sensor_id]
        
        # Check if sensor is reachable - intentional skip, no retry
        if not sensor_data.get('config', {}).get('reachable', False):
            logger.warning(f"Sensor {sensor_info['location']} is offline, skipping")
            return None
        
        # Get temperature from state - intentional skip, no retry
        raw_temp = sensor_data.get('state', {}).get('temperature')
        if raw_temp is None:
            logger.warning(f"No temperature data for sensor {sensor_info['location']}")
            return None
        
        # Convert and validate temperature
        temp_celsius = convert_temperature(raw_temp)
        is_anomalous = is_temperature_anomalous(temp_celsius, config)
        
        if is_anomalous:
            logger.warning(f"Anomalous temperature reading: {temp_celsius}°C at {sensor_info['location']}")
        
        # Build reading dictionary
        reading = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'device_id': f"hue:{sensor_info['unique_id']}",
            'temperature_celsius': temp_celsius,
            'location': sensor_info['location'],
            'device_type': 'hue_sensor',
            'is_anomalous': is_anomalous,
        }
        
        # Add optional metadata if configured
        hue_config = config.get('collectors', {}).get('hue', {})
        
        if hue_config.get('collect_battery_level', True):
            battery = sensor_data.get('config', {}).get('battery')
            if battery is not None:
                reading['battery_level'] = battery
        
        if hue_config.get('collect_signal_strength', True):
            # Map reachable to signal strength (1=reachable, 0=unreachable)
            reading['signal_strength'] = 1 if sensor_data.get('config', {}).get('reachable') else 0
        
        if hue_config.get('collect_raw_response', False):
            reading['raw_response'] = json.dumps(sensor_data)
        
        return reading
        
    except requests.RequestException as e:
        # Network/API errors - raise to allow retry
        logger.debug(f"Transient error collecting from sensor {sensor_info['location']}: {e}")
        raise
    except Exception as e:
        # Other errors - log and return None (no retry)
        logger.error(f"Failed to collect from sensor {sensor_info['location']}: {e}")
        return None


def collect_all_readings(bridge: Bridge, config: dict) -> List[Dict]:
    """
    Collect temperature readings from all available sensors.
    
    Args:
        bridge: Connected Bridge object
        config: Configuration dictionary
        
    Returns:
        List of reading dictionaries
    """
    logger.info("Starting collection cycle...")
    
    # Discover sensors
    sensors = discover_sensors(bridge, config)
    
    if not sensors:
        logger.warning("No temperature sensors found")
        return []
    
    readings = []
    hue_config = config.get('collectors', {}).get('hue', {})
    retry_attempts = hue_config.get('retry_attempts', 3)
    retry_backoff = hue_config.get('retry_backoff_base', 2)
    
    # Fetch sensors data once per cycle (API optimization)
    api_key = bridge.username if hasattr(bridge, 'username') else None
    bridge_ip = bridge.ip if hasattr(bridge, 'ip') else None
    cached_sensors_data = None
    
    if api_key and bridge_ip:
        try:
            start_time = time.time()
            response = requests.get(f"http://{bridge_ip}/api/{api_key}/sensors", timeout=10)
            response.raise_for_status()
            cached_sensors_data = response.json()
            duration_ms = int((time.time() - start_time) * 1000)
            response_size = sys.getsizeof(response.text)
            logger.info(f"API optimization: fetched all sensors in {duration_ms}ms ({response_size} bytes)")
        except Exception as e:
            logger.warning(f"Failed to cache sensors data, will use per-sensor calls: {e}")
            cached_sensors_data = None

    for sensor_info in sensors:
        sensor_id = sensor_info['sensor_id']
        
        # Retry logic with exponential backoff for transient errors only
        for attempt in range(retry_attempts):
            try:
                reading = collect_reading_from_sensor(
                    bridge, sensor_id, sensor_info, config, cached_sensors_data
                )
                
                if reading:
                    readings.append(reading)
                    logger.info(f"✓ Collected: {sensor_info['location']} = {reading['temperature_celsius']:.2f}°C")
                    break  # Success, no need to retry
                else:
                    # None means sensor offline or no data - intentional skip, don't retry
                    break
                    
            except requests.RequestException as e:
                # Transient network/API error - retry with backoff
                if attempt < retry_attempts - 1:
                    wait_time = retry_backoff ** attempt
                    logger.warning(
                        f"Transient error for {sensor_info['location']} "
                        f"(attempt {attempt + 1}/{retry_attempts}), retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Collection failed for {sensor_info['location']} "
                        f"after {retry_attempts} attempts: {e}"
                    )
            except Exception as e:
                # Non-transient error - log and move on
                logger.error(f"Non-retryable error for {sensor_info['location']}: {e}")
                break
    
    logger.info(f"Collection cycle complete: {len(readings)}/{len(sensors)} sensors")
    return readings


def store_readings(readings: List[Dict], config: dict):
    """
    Store readings in database.
    
    Args:
        readings: List of reading dictionaries
        config: Configuration dictionary
    """
    if not readings:
        logger.info("No readings to store")
        return
    
    # Import here to avoid circular dependency
    from source.storage.manager import DatabaseManager
    
    db_path = config.get('storage', {}).get('database_path', 'data/readings.db')
    # Pass config to DatabaseManager so it uses configured retry/timeout settings
    db = DatabaseManager(db_path, config)
    
    success_count = 0
    duplicate_count = 0
    error_count = 0
    
    for reading in readings:
        try:
            result = db.insert_temperature_reading(reading)
            if result:
                success_count += 1
            else:
                duplicate_count += 1
                logger.debug(f"Duplicate reading skipped: {reading['device_id']} at {reading['timestamp']}")
        except Exception as e:
            error_count += 1
            logger.error(f"Database error for {reading['location']}: {e}")
    
    db.close()
    
    logger.info(f"Storage complete: {success_count} stored, {duplicate_count} duplicates, {error_count} errors")


def main():
    """Main collector entry point."""
    parser = argparse.ArgumentParser(
        description='Collect temperature data from Philips Hue sensors',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover all temperature sensors
  python source/collectors/hue_collector.py --discover
  
  # Collect readings once
  python source/collectors/hue_collector.py --collect-once
  
  # Continuous collection (every 5 minutes by default)
  python source/collectors/hue_collector.py --continuous
        """
    )
    parser.add_argument(
        '--discover',
        action='store_true',
        help='Discover and list all temperature sensors'
    )
    parser.add_argument(
        '--collect-once',
        action='store_true',
        help='Collect readings once and exit'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Collect readings continuously at configured interval'
    )
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to config file'
    )
    parser.add_argument(
        '--secrets',
        default='config/secrets.yaml',
        help='Path to secrets file'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    secrets = load_secrets(args.secrets)
    
    # Connect to Bridge
    bridge = connect_to_bridge(config, secrets)
    
    # Execute requested action
    if args.discover:
        logger.info("=" * 70)
        logger.info("TEMPERATURE SENSOR DISCOVERY")
        logger.info("=" * 70)
        sensors = discover_sensors(bridge, config)
        
        if sensors:
            print("\n" + "=" * 80)
            print("🌡️  DISCOVERED TEMPERATURE SENSORS")
            print("=" * 80 + "\n")
            for i, sensor in enumerate(sensors, 1):
                status_icon = "✅" if sensor['is_reachable'] else "⚠️"
                battery = sensor['battery_level'] if sensor['battery_level'] else None
                
                # Color and status
                if sensor['is_reachable']:
                    status = "Online"
                else:
                    status = "Offline"
                
                # Battery color
                if battery:
                    if battery >= 75:
                        batt_emoji = "🟢"
                    elif battery >= 50:
                        batt_emoji = "🟡"
                    else:
                        batt_emoji = "🔴"
                    battery_str = f"{batt_emoji} {battery}%"
                else:
                    battery_str = "N/A"
                
                print(f"{status_icon} Sensor {i}: {sensor['location']}")
                print(f"   Status: {status}")
                print(f"   Device ID: {sensor['unique_id'][:20]}...")
                print(f"   Model: {sensor['model_id']}")
                print(f"   Battery: {battery_str}")
                print()
            
            print("=" * 80)
            print(f"📊 Total: {len(sensors)} sensor(s) found\n")
        
    elif args.collect_once:
        logger.info("=" * 70)
        logger.info("SINGLE COLLECTION CYCLE")
        logger.info("=" * 70)
        readings = collect_all_readings(bridge, config)
        
        # Pretty print results
        print("\n" + "=" * 80)
        print("📈 COLLECTION RESULTS")
        print("=" * 80 + "\n")
        
        if readings:
            for reading in readings:
                anomaly_icon = "⚠️" if reading.get('is_anomalous') else "✅"
                temp = reading.get('temperature_celsius', 'N/A')
                location = reading.get('location', 'Unknown')
                battery = reading.get('battery_level')
                
                print(f"{anomaly_icon} {location}: {temp:.2f}°C", end="")
                if battery:
                    print(f" [Battery: {battery}%]", end="")
                print()
            
            print(f"\n✨ Collected {len(readings)} reading(s)")
        
        print("\n" + "=" * 80)
        store_readings(readings, config)
        
    elif args.continuous:
        logger.info("=" * 70)
        logger.info("CONTINUOUS COLLECTION MODE")
        logger.info("=" * 70)
        
        hue_config = config.get('collectors', {}).get('hue', {})
        interval = hue_config.get('collection_interval', 300)
        
        logger.info(f"Collection interval: {interval} seconds ({interval/60:.1f} minutes)")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 70)
        
        try:
            while True:
                readings = collect_all_readings(bridge, config)
                store_readings(readings, config)
                
                logger.info(f"Waiting {interval} seconds until next collection...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\nCollection stopped by user")
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
