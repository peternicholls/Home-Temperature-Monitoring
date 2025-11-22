#!/usr/bin/env python3
"""
Nest Thermostat via Amazon Alexa - Main Collection Script

Handles discovery and continuous collection of Nest thermostat data through Alexa APIs.
Supports three modes:
  - --discover: List all Nest thermostats
  - --collect-once: Single collection cycle
  - --continuous: Continuous polling (default 5-minute intervals)

Usage:
  python -m source.collectors.nest_via_amazon_collector_main --discover
  python -m source.collectors.nest_via_amazon_collector_main --collect-once
  python -m source.collectors.nest_via_amazon_collector_main --continuous
"""

import asyncio
import argparse
import json
import time
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from source.collectors.nest_via_amazon_collector import NestViaAmazonCollector
from source.config.loader import load_config, load_secrets
from source.storage.manager import DatabaseManager
from source.storage.yaml_device_registry import YAMLDeviceRegistry
from source.utils.structured_logger import StructuredLogger

# Configure structured logging
logger: Optional[StructuredLogger] = None  # Will be initialized in main() with config


async def discover_devices(config: dict, secrets: dict) -> bool:
    """
    Discover and list all Nest thermostats via Alexa.
    
    Args:
        config: Configuration dictionary
        secrets: Secrets dictionary with Amazon cookies
        
    Returns:
        bool: True if devices were found, False otherwise
    """
    try:
        cookies = secrets.get('amazon_aqm', {}).get('cookies', {})
        if not cookies:
            if logger:
                logger.error("No Amazon cookies found in secrets.yaml. Run 'make web-start' first.")
            return False
        
        collector = NestViaAmazonCollector(cookies, config, logger)
        
        if logger:
            logger.info("Discovering Nest thermostats via Alexa...")
        devices = await collector.list_devices()
        
        if not devices:
            if logger:
                logger.warning("No Nest thermostats found")
            return False
        
        if logger:
            logger.info(f"Found {len(devices)} Nest thermostat(s)")
        print("\n" + "=" * 80)
        print("NEST THERMOSTATS DISCOVERED")
        print("=" * 80)
        
        for i, device in enumerate(devices, 1):
            print(f"\n{i}. {device['friendly_name']}")
            print(f"   Device ID: {device['device_id']}")
            print(f"   Appliance ID: {device['appliance_id']}")
            print(f"   Manufacturer: {device['manufacturer']}")
            print(f"   Model: {device['model_name']}")
            print(f"   Capabilities: {len(device['capabilities'])} interfaces")
            
            # List capabilities
            for cap in device['capabilities']:
                iface = cap.get('interfaceName', 'Unknown')
                print(f"     - {iface}")
        
        print("\n" + "=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"Discovery failed: {e}", exc_info=True)
        return False


async def collect_once(config: dict, secrets: dict) -> bool:
    """
    Perform a single collection cycle.
    
    Args:
        config: Configuration dictionary
        secrets: Secrets dictionary with Amazon cookies
        
    Returns:
        bool: True if collection successful, False otherwise
    """
    try:
        cookies = secrets.get('amazon_aqm', {}).get('cookies', {})
        if not cookies:
            if logger:
                logger.error("No Amazon cookies found in secrets.yaml. Run 'make web-start' first.")
            return False
        
        # Initialize collector, database, and device registry
        collector = NestViaAmazonCollector(cookies, config, logger)
        db_manager = DatabaseManager(db_path=config.get('database', {}).get('path', 'data/readings.db'))
        registry_manager = YAMLDeviceRegistry()
        
        if logger:
            logger.info("Starting single Nest collection cycle...")
        
        # Discover devices
        if logger:
            logger.info("Discovering Nest devices (attempt 1/3)")
        devices = await collector.list_devices()
        if not devices:
            if logger:
                logger.error("No Nest thermostats found")
            return False
        
        # Collect from each device
        success_count = 0
        for device in devices:
            appliance_id = device['appliance_id']
            device_id = device['device_id']
            friendly_name = device['friendly_name']
            model_name = device.get('model_name', 'Nest Thermostat')
            
            # Register device in registry
            registry_manager.register_device(
                unique_id=device_id,
                location=friendly_name,
                device_type='nest_thermostat',
                model_info=model_name
            )
            
            # Get custom name from registry (if set by user)
            custom_name = registry_manager.get_device_name(device_id)
            display_name = custom_name if custom_name else friendly_name
            
            if logger:
                logger.info(f"Found Nest thermostat: {friendly_name} ({device_id})")
            
            if logger:
                logger.info(f"Collecting from: {display_name}")
            
            # Get readings
            if logger:
                logger.info("Fetching thermostat readings (attempt 1/3)")
            readings = await collector.get_thermostat_readings(appliance_id)
            if not readings:
                if logger:
                    logger.error(f"Failed to get readings from {display_name}")
                continue
            
            # Log collected readings
            if logger:
                logger.info("Collected readings from Nest thermostat")
            
            # Validate
            errors = collector.validate_readings(readings)
            if errors:
                if logger:
                    logger.warning(f"Validation warnings for {display_name}: {errors}")
            
            # Format for database (use custom name if available)
            db_reading = collector.format_reading_for_db(device_id, display_name, readings, config)
            
            # Log the reading
            if logger:
                logger.info(f"Reading: {display_name}")
                logger.info(f"  Temperature: {readings.get('temperature_celsius')}°C")
                logger.info(f"  Mode: {readings.get('thermostat_mode')}")
                logger.info(f"  Timestamp: {readings.get('timestamp')}")
            
            # Store in database
            if db_manager.insert_temperature_reading(db_reading):
                if logger:
                    logger.info(f"Stored reading for {display_name}")
                success_count += 1
            else:
                if logger:
                    logger.debug(f"Duplicate reading for {display_name}, skipped")
        
        if success_count > 0:
            if logger:
                logger.info(f"Collection successful! Stored {success_count} reading(s)")
            return True
        else:
            if logger:
                logger.error("No readings were stored")
            return False
            
    except Exception as e:
        if logger:
            logger.error(f"Collection failed: {e}", exc_info=True)
        return False


async def collect_continuous(config: dict, secrets: dict) -> None:
    """
    Continuous collection loop.
    
    Args:
        config: Configuration dictionary
        secrets: Secrets dictionary with Amazon cookies
    """
    try:
        cookies = secrets.get('amazon_aqm', {}).get('cookies', {})
        if not cookies:
            if logger:
                logger.error("No Amazon cookies found in secrets.yaml. Run 'make web-start' first.")
            return
        
        # Get collection interval from config (default 300 seconds = 5 minutes)
        collection_config = config.get('collection', {})
        interval = collection_config.get('interval', 300)
        
        # Initialize collector, database, and device registry
        collector = NestViaAmazonCollector(cookies, config, logger)
        db_manager = DatabaseManager(db_path=config.get('database', {}).get('path', 'data/readings.db'))
        registry_manager = YAMLDeviceRegistry()
        
        if logger:
            logger.info(f"Starting continuous Nest collection (interval: {interval}s)...")
            logger.info("Press Ctrl+C to stop")
        
        cycle = 0
        while True:
            cycle += 1
            if logger:
                logger.info(f"\n{'=' * 80}")
                logger.info(f"Collection Cycle {cycle} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'=' * 80}")
            
            try:
                # Discover devices
                devices = await collector.list_devices()
                if not devices:
                    if logger:
                        logger.warning("No Nest thermostats found, skipping cycle")
                    await asyncio.sleep(interval)
                    continue
                
                # Collect from each device
                success_count = 0
                for device in devices:
                    appliance_id = device['appliance_id']
                    device_id = device['device_id']
                    friendly_name = device['friendly_name']
                    model_name = device.get('model_name', 'Nest Thermostat')
                    
                    # Register device in registry
                    registry_manager.register_device(
                        unique_id=device_id,
                        location=friendly_name,
                        device_type='nest_thermostat',
                        model_info=model_name
                    )
                    
                    # Get custom name from registry (if set by user)
                    custom_name = registry_manager.get_device_name(device_id)
                    display_name = custom_name if custom_name else friendly_name
                    
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
                            logger.warning(f"Validation warnings: {errors}")
                    
                    # Format for database (use custom name if available)
                    db_reading = collector.format_reading_for_db(device_id, display_name, readings, config)
                    
                    # Store in database
                    if db_manager.insert_temperature_reading(db_reading):
                        if logger:
                            logger.info(f"✓ {display_name}: {readings.get('temperature_celsius')}°C ({readings.get('thermostat_mode')})")
                        success_count += 1
                    else:
                        if logger:
                            logger.debug(f"Duplicate reading for {display_name}")
                
                if success_count > 0:
                    if logger:
                        logger.info(f"Cycle {cycle} complete: {success_count} reading(s) stored")
                else:
                    pass  # Already logged warnings above
                
            except Exception as e:
                if logger:
                    logger.error(f"Cycle {cycle} error: {e}", exc_info=True)
            
            # Wait for next cycle
            if logger:
                logger.info(f"Next collection in {interval}s...")
            await asyncio.sleep(interval)
            
    except KeyboardInterrupt:
        if logger:
            logger.info("Collection stopped by user")
    except Exception as e:
        if logger:
            logger.error(f"Continuous collection failed: {e}", exc_info=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Nest Thermostat Data Collector via Amazon Alexa",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m source.collectors.nest_via_amazon_collector_main --discover
  python -m source.collectors.nest_via_amazon_collector_main --collect-once
  python -m source.collectors.nest_via_amazon_collector_main --continuous
        """
    )
    
    parser.add_argument(
        '--discover',
        action='store_true',
        help='Discover Nest thermostats and list their details'
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
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config()
        secrets = load_secrets()
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)
    
    # Configure logger with config
    config['component'] = 'nest_via_amazon_collector'
    global logger
    logger = StructuredLogger(config)
    
    # Determine which action to take
    if args.discover:
        success = asyncio.run(discover_devices(config, secrets))
        sys.exit(0 if success else 1)
    
    elif args.collect_once:
        success = asyncio.run(collect_once(config, secrets))
        sys.exit(0 if success else 1)
    
    elif args.continuous:
        asyncio.run(collect_continuous(config, secrets))
        sys.exit(0)
    
    else:
        # Default to discover if no args given
        success = asyncio.run(discover_devices(config, secrets))
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
