#!/usr/bin/env python3
"""
Amazon/Alexa Unified Collector - Main Script

Unified collection script for ALL Amazon/Alexa smart home devices:
- Amazon Smart Air Quality Monitors
- Nest Thermostats via Alexa
- Any other temperature-capable devices

Single GraphQL discovery call = 50% reduction in API calls vs separate collectors.

Usage:
    python -m source.collectors.amazon_unified_collector_main --discover
    python -m source.collectors.amazon_unified_collector_main --collect-once
    python -m source.collectors.amazon_unified_collector_main --continuous
"""

import asyncio
import argparse
import yaml
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from source.collectors.amazon_unified_collector import AmazonUnifiedCollector
from source.collectors.amazon_auth import validate_amazon_cookies, check_cookie_expiration
from source.storage.manager import DatabaseManager
from source.storage.yaml_device_registry import YAMLDeviceRegistry
from source.config.loader import load_config
from source.utils.structured_logger import StructuredLogger

# Configure structured logging
logger: Optional[StructuredLogger] = None  # Will be initialized in main() with config


async def discover_devices(cookies: dict, config: dict):
    """
    Discover and list all Amazon/Alexa devices.
    
    Args:
        cookies: Amazon authentication cookies
        config: Configuration dictionary
    """
    try:
        start_time = time.time()
        collector = AmazonUnifiedCollector(cookies, config, logger)
        devices = await collector.list_devices()
        discovery_duration_ms = int((time.time() - start_time) * 1000)
        
        if not devices:
            if logger:
                logger.warning(
                    "Device discovery complete",
                    device_count=0,
                    reason="no_devices_found",
                    discovery_duration_ms=discovery_duration_ms
                )
            print("\n⚠️  No Amazon/Alexa devices found")
            return
        
        # Group by device type
        aqm_devices = [d for d in devices if d['device_type'] == 'alexa_aqm']
        nest_devices = [d for d in devices if d['device_type'] == 'nest_thermostat']
        
        if logger:
            logger.success(
                "Device discovery complete",
                device_count=len(devices),
                aqm_count=len(aqm_devices),
                nest_count=len(nest_devices),
                discovery_duration_ms=discovery_duration_ms
            )
        
        print("\n" + "=" * 80)
        print("AMAZON/ALEXA DEVICES DISCOVERED")
        print("=" * 80)
        print(f"\nTotal: {len(devices)} device(s)")
        print(f"  • Amazon AQM: {len(aqm_devices)}")
        print(f"  • Nest Thermostats: {len(nest_devices)}")
        print(f"\nDiscovery time: {discovery_duration_ms}ms")
        
        if aqm_devices:
            print("\n" + "-" * 80)
            print("AMAZON AIR QUALITY MONITORS")
            print("-" * 80)
            for i, device in enumerate(aqm_devices, 1):
                print(f"\n{i}. {device['friendly_name']}")
                print(f"   Device ID: {device['device_id']}")
                print(f"   Serial: {device['device_serial']}")
                print(f"   Entity ID: {device['entity_id']}")
        
        if nest_devices:
            print("\n" + "-" * 80)
            print("NEST THERMOSTATS")
            print("-" * 80)
            for i, device in enumerate(nest_devices, 1):
                print(f"\n{i}. {device['friendly_name']}")
                print(f"   Device ID: {device['device_id']}")
                print(f"   Manufacturer: {device['manufacturer']}")
                print(f"   Model: {device['model_name']}")
        
        print("\n" + "=" * 80 + "\n")
        
    except Exception as e:
        if logger:
            logger.error(
                f"Error during device discovery: {e}",
                error_code="DISCOVERY_FAILED",
                error_message=str(e),
                exc_info=True
            )


async def collect_once(cookies: dict, config: dict, db_manager: DatabaseManager):
    """
    Collect data once from all devices and store in database.
    
    Args:
        cookies: Amazon authentication cookies
        config: Configuration dictionary
        db_manager: DatabaseManager instance
    """
    try:
        start_time = time.time()
        collector = AmazonUnifiedCollector(cookies, config, logger)
        registry_manager = YAMLDeviceRegistry()
        
        # Discover all devices
        if logger:
            logger.info("Discovering Amazon/Alexa devices...")
        devices = await collector.list_devices()
        
        if not devices:
            if logger:
                logger.warning("No devices found")
            return False
        
        if logger:
            logger.info(f"Found {len(devices)} device(s): {sum(1 for d in devices if d['device_type'] == 'alexa_aqm')} AQM, {sum(1 for d in devices if d['device_type'] == 'nest_thermostat')} Nest")
        
        # Collect from each device
        success_count = 0
        for device in devices:
            device_type = device['device_type']
            device_id = device['device_id']
            friendly_name = device['friendly_name']
            
            try:
                if device_type == 'alexa_aqm':
                    # Amazon AQM collection
                    entity_id = device['entity_id']
                    model_name = "Amazon Smart Air Quality Monitor"
                    
                    # Register device
                    registry_manager.register_device(
                        unique_id=device_id,
                        location=friendly_name,
                        device_type='alexa_aqm',
                        model_info=model_name
                    )
                    
                    # Get custom name
                    custom_name = registry_manager.get_device_name(device_id)
                    display_name = custom_name if custom_name else friendly_name
                    
                    if logger:
                        logger.info(f"Collecting AQM data from: {display_name}")
                    
                    # Get readings
                    readings = await collector.get_air_quality_readings(entity_id)
                    if not readings:
                        if logger:
                            logger.error(f"Failed to get readings from {display_name}")
                        continue
                    
                    # Validate
                    errors = collector.validate_readings(readings)
                    if errors:
                        if logger:
                            logger.warning(f"Validation warnings for {display_name}: {errors}")
                    
                    # Format for database (AQM-specific method)
                    db_reading = collector.format_aqm_reading_for_db(entity_id, device['device_serial'], readings, config, registry_manager)
                    
                    # Log collected data
                    if logger:
                        logger.info(f"  Temperature: {readings.get('temperature_celsius')}°C, Humidity: {readings.get('humidity_percent')}%")
                    
                    # Store
                    if db_manager.insert_temperature_reading(db_reading):
                        if logger:
                            logger.info(f"✓ Stored reading for {display_name}")
                        success_count += 1
                    else:
                        if logger:
                            logger.debug(f"Duplicate reading for {display_name}, skipped")
                
                elif device_type == 'nest_thermostat':
                    # Nest thermostat collection
                    appliance_id = device['appliance_id']
                    model_name = device.get('model_name', 'Nest Thermostat')
                    
                    # Register device
                    registry_manager.register_device(
                        unique_id=device_id,
                        location=friendly_name,
                        device_type='nest_thermostat',
                        model_info=model_name
                    )
                    
                    # Get custom name
                    custom_name = registry_manager.get_device_name(device_id)
                    display_name = custom_name if custom_name else friendly_name
                    
                    if logger:
                        logger.info(f"Collecting Nest data from: {display_name}")
                    
                    # Get readings
                    readings = await collector.get_thermostat_readings(appliance_id)
                    if not readings:
                        if logger:
                            logger.error(f"Failed to get readings from {display_name}")
                        continue
                    
                    # Validate
                    errors = collector.validate_readings(readings)
                    if errors:
                        if logger:
                            logger.warning(f"Validation warnings for {display_name}: {errors}")
                    
                    # Format for database (Nest-specific method)
                    db_reading = collector.format_nest_reading_for_db(device_id, friendly_name, readings, config, registry_manager)
                    
                    # Log collected data
                    if logger:
                        logger.info(f"  Temperature: {readings.get('temperature_celsius')}°C, Mode: {readings.get('thermostat_mode')}")
                    
                    # Store
                    if db_manager.insert_temperature_reading(db_reading):
                        if logger:
                            logger.info(f"✓ Stored reading for {display_name}")
                        success_count += 1
                    else:
                        if logger:
                            logger.debug(f"Duplicate reading for {display_name}, skipped")
            
            except Exception as e:
                if logger:
                    logger.error(f"Error collecting from {friendly_name}: {e}", exc_info=True)
                continue
        
        cycle_duration_ms = int((time.time() - start_time) * 1000)
        
        if success_count > 0:
            if logger:
                logger.success(
                    "Collection completed successfully",
                    cycle_duration_ms=cycle_duration_ms,
                    stored_count=success_count,
                    status="success"
                )
            return True
        else:
            if logger:
                logger.warning(
                    "Collection completed with no new data",
                    cycle_duration_ms=cycle_duration_ms,
                    status="partial"
                )
            return False
        
    except Exception as e:
        if logger:
            logger.error(
                f"Collection failed: {e}",
                error_code="COLLECTION_FAILED",
                error_message=str(e),
                exc_info=True
            )
        return False


async def collect_continuous(cookies: dict, config: dict, db_manager: DatabaseManager):
    """
    Continuous collection loop for all Amazon/Alexa devices.
    
    Args:
        cookies: Amazon authentication cookies
        config: Configuration dictionary
        db_manager: DatabaseManager instance
    """
    amazon_config = config.get('amazon_aqm', {})
    collection_interval = amazon_config.get('collection_interval', 300)  # Default 5 minutes
    retry_attempts = amazon_config.get('retry_attempts', 3)
    retry_backoff_base = amazon_config.get('retry_backoff_base', 1.0)
    
    if logger:
        logger.info(f"Starting unified continuous collection, interval {collection_interval}s")
        logger.info("Press Ctrl+C to stop")
    
    cycle_count = 0
    total_errors = 0
    
    try:
        while True:
            cycle_count += 1
            cycle_start = time.time()
            
            if logger:
                logger.info(f"\n{'=' * 80}")
                logger.info(f"Collection Cycle {cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'=' * 80}")
            
            # Attempt collection with retries
            success = False
            for attempt in range(1, retry_attempts + 1):
                try:
                    if attempt > 1 and logger:
                        logger.info(f"Retry attempt {attempt}/{retry_attempts}")
                    
                    success = await collect_once(cookies, config, db_manager)
                    
                    if success:
                        break  # Success, exit retry loop
                    
                    if attempt < retry_attempts:
                        wait_time = retry_backoff_base * (2 ** (attempt - 1))
                        if logger:
                            logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                
                except Exception as e:
                    total_errors += 1
                    if logger:
                        logger.error(f"Attempt {attempt} failed: {e}", exc_info=True)
                    
                    if attempt < retry_attempts:
                        wait_time = retry_backoff_base * (2 ** (attempt - 1))
                        if logger:
                            logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
            
            cycle_duration = int(time.time() - cycle_start)
            
            if not success:
                if logger:
                    logger.error(f"Cycle {cycle_count} failed after {retry_attempts} attempts")
            
            # Wait for next cycle
            if logger:
                logger.info(f"Cycle {cycle_count} complete in {cycle_duration}s")
                logger.info(f"Next collection in {collection_interval}s...")
            
            await asyncio.sleep(collection_interval)
    
    except KeyboardInterrupt:
        if logger:
            logger.info(f"\nCollection stopped by user after {cycle_count} cycles")
            logger.info(f"Total errors: {total_errors}")
    except Exception as e:
        if logger:
            logger.error(f"Continuous collection failed: {e}", exc_info=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Amazon/Alexa Device Collector (AQM + Nest + more)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m source.collectors.amazon_unified_collector_main --discover
  python -m source.collectors.amazon_unified_collector_main --collect-once
  python -m source.collectors.amazon_unified_collector_main --continuous
        """
    )
    
    parser.add_argument(
        '--discover',
        action='store_true',
        help='Discover all Amazon/Alexa devices and list their details'
    )
    parser.add_argument(
        '--collect-once',
        action='store_true',
        help='Perform a single collection cycle'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuous collection (Ctrl+C to stop)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to config file (default: config/config.yaml)'
    )
    parser.add_argument(
        '--secrets',
        type=str,
        default='config/secrets.yaml',
        help='Path to secrets file (default: config/secrets.yaml)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load config from {args.config}: {e}")
        sys.exit(1)
    
    # Initialize logger with config
    config['component'] = 'amazon_unified_collector'
    global logger
    logger = StructuredLogger(config)
    
    # Load secrets (cookies)
    try:
        with open(args.secrets, 'r') as f:
            secrets = yaml.safe_load(f)
        cookies = secrets.get('amazon_aqm', {}).get('cookies', {})
    except Exception as e:
        logger.error(f"Failed to load secrets from {args.secrets}: {e}")
        sys.exit(1)
    
    # Validate cookies
    is_valid, errors = validate_amazon_cookies(cookies)
    if not is_valid:
        logger.error(f"Invalid Amazon cookies: {errors}")
        print("\n❌ Amazon cookies are invalid or expired")
        print("   Run 'make web-start' to refresh authentication")
        sys.exit(1)
    
    # Check cookie expiration
    is_expired, warning = check_cookie_expiration(cookies)
    if is_expired:
        logger.warning(
            "Cookie expiration warning",
            is_expired=True,
            warning_message=warning
        )
    
    # IMPORTANT: Copy collectors.amazon_aqm to top level for collector access
    # Also preserve collectors.general for shared settings like fallback_location
    if 'collectors' in config and 'amazon_aqm' in config['collectors']:
        config['amazon_aqm'] = config['collectors']['amazon_aqm']
        # Note: Keep collectors.general intact - it's used by format methods
    
    # Determine which action to take
    if args.discover:
        asyncio.run(discover_devices(cookies, config))
        sys.exit(0)
    
    elif args.collect_once:
        db_path = config.get('storage', {}).get('database_path', 'data/readings.db')
        db_manager = DatabaseManager(db_path=db_path)
        success = asyncio.run(collect_once(cookies, config, db_manager))
        sys.exit(0 if success else 1)
    
    elif args.continuous:
        db_path = config.get('storage', {}).get('database_path', 'data/readings.db')
        db_manager = DatabaseManager(db_path=db_path)
        asyncio.run(collect_continuous(cookies, config, db_manager))
        sys.exit(0)
    
    else:
        # Default to discover if no args given
        asyncio.run(discover_devices(cookies, config))
        sys.exit(0)


if __name__ == '__main__':
    main()
