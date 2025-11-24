#!/usr/bin/env python3
"""
Amazon Alexa Unified Collector - Main Entry Point

Collects data from ALL Amazon/Alexa smart home devices:
- Amazon Smart Air Quality Monitors
- Nest Thermostats
- Any other temperature-capable devices

Features:
- Single collection cycle for all devices (efficient)
- Automatic device discovery
- Parallel state fetching
- Cookie-based authentication
- Comprehensive logging

Usage:
    python amazon_alexa_collector_main.py --discover       # List all devices
    python amazon_alexa_collector_main.py --collect-once   # Single collection run
    python amazon_alexa_collector_main.py                  # Production mode

Sprint: 005-system-reliability
Enhancement: Unified collector replacing amazon_aqm_collector and nest_via_amazon_collector
"""

import asyncio
import sys
import yaml
from pathlib import Path
from datetime import datetime, timezone

# Add source directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from source.collectors.amazon_alexa_collector import AmazonAlexaCollector
from source.collectors.amazon_auth import validate_amazon_cookies, check_cookie_expiration
from source.config.loader import load_config
from source.storage.manager import DatabaseManager
from source.utils.structured_logger import StructuredLogger


async def discover_devices(collector: AmazonAlexaCollector, logger: StructuredLogger):
    """
    Discover and display all Amazon/Alexa devices.
    
    Args:
        collector: AmazonAlexaCollector instance
        logger: StructuredLogger instance
    """
    logger.info("Starting device discovery...")
    
    devices = await collector.discover_all_devices()
    
    if not devices:
        logger.warning("No devices discovered")
        return
    
    # Group by device type
    by_type = {}
    for device in devices:
        dtype = device['device_type']
        if dtype not in by_type:
            by_type[dtype] = []
        by_type[dtype].append(device)
    
    # Display summary
    print("\n" + "="*80)
    print(f"DISCOVERED {len(devices)} AMAZON/ALEXA DEVICES")
    print("="*80 + "\n")
    
    for dtype, devices_list in sorted(by_type.items()):
        print(f"\n{dtype.upper().replace('_', ' ')} ({len(devices_list)} devices):")
        print("-" * 80)
        
        for device in devices_list:
            print(f"  • {device['friendly_name']}")
            print(f"    ID: {device['device_id']}")
            print(f"    Serial: {device['device_serial']}")
            print(f"    Manufacturer: {device['manufacturer']}")
            if device.get('model_name'):
                print(f"    Model: {device['model_name']}")
            print()
    
    print("="*80 + "\n")
    logger.info("Device discovery complete", total=len(devices))


async def collect_once(collector: AmazonAlexaCollector, db_manager: DatabaseManager, logger: StructuredLogger):
    """
    Run a single collection cycle for all devices.
    
    Args:
        collector: AmazonAlexaCollector instance
        db_manager: DatabaseManager instance
        logger: StructuredLogger instance
    """
    logger.info("Starting single collection cycle...")
    
    readings = await collector.collect_all_readings()
    
    if not readings:
        logger.warning("No readings collected")
        return
    
    # Store all readings
    stored_count = 0
    failed_count = 0
    
    for reading in readings:
        try:
            db_manager.insert_reading(reading)
            stored_count += 1
            logger.debug(f"Stored reading", device_id=reading['device_id'], type=reading['device_type'])
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to store reading", device_id=reading['device_id'], error=str(e))
    
    # Summary
    print("\n" + "="*80)
    print(f"COLLECTION COMPLETE: {stored_count} stored, {failed_count} failed")
    print("="*80 + "\n")
    
    logger.info(
        "Collection cycle complete",
        total_readings=len(readings),
        stored=stored_count,
        failed=failed_count
    )


async def collect_continuous(collector: AmazonAlexaCollector, db_manager: DatabaseManager, logger: StructuredLogger, interval: int = 300):
    """
    Run continuous collection cycles.
    
    Args:
        collector: AmazonAlexaCollector instance
        db_manager: DatabaseManager instance
        logger: StructuredLogger instance
        interval: Seconds between collection cycles (default: 300 = 5 minutes)
    """
    logger.info(f"Starting continuous collection", interval_seconds=interval)
    
    cycle_count = 0
    
    while True:
        cycle_count += 1
        cycle_start = datetime.now(timezone.utc)
        
        logger.info(f"Starting collection cycle", cycle=cycle_count)
        
        try:
            readings = await collector.collect_all_readings()
            
            if readings:
                stored_count = 0
                failed_count = 0
                
                for reading in readings:
                    try:
                        db_manager.insert_reading(reading)
                        stored_count += 1
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Failed to store reading", device_id=reading['device_id'], error=str(e))
                
                logger.info(
                    f"Cycle {cycle_count} complete",
                    total_readings=len(readings),
                    stored=stored_count,
                    failed=failed_count
                )
            else:
                logger.warning(f"Cycle {cycle_count}: No readings collected")
        
        except Exception as e:
            logger.error(f"Cycle {cycle_count} failed", error=str(e), exc_info=True)
        
        # Calculate sleep time
        cycle_duration = (datetime.now(timezone.utc) - cycle_start).total_seconds()
        sleep_time = max(0, interval - cycle_duration)
        
        if sleep_time > 0:
            logger.debug(f"Sleeping until next cycle", sleep_seconds=sleep_time)
            await asyncio.sleep(sleep_time)


async def main():
    """Main entry point for Amazon Alexa unified collector."""
    
    # Load configuration
    config = load_config()
    config['component'] = 'amazon_alexa_collector'
    logger = StructuredLogger(config)
    
    logger.info("Amazon Alexa Unified Collector starting...")
    
    # Load cookies from secrets
    try:
        import yaml
        with open('config/secrets.yaml', 'r') as f:
            secrets = yaml.safe_load(f)
        cookies = secrets.get('amazon_aqm', {}).get('cookies', {})
    except Exception as e:
        logger.error(f"Failed to load secrets: {e}", exc_info=True)
        sys.exit(1)
    
    # Validate cookies
    is_valid, errors = validate_amazon_cookies(cookies)
    if not is_valid:
        logger.error("❌ Cookie validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("\nPlease re-authenticate using the web UI:")
        logger.error("  1. Run: python source/web/app.py")
        logger.error("  2. Navigate to: http://localhost:5001/setup")
        logger.error("  3. Click 'Connect Amazon Account' and log in")
        sys.exit(1)
    
    # Initialize collector
    collector = AmazonAlexaCollector(cookies, config, logger)
    
    # Parse command-line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == '--discover':
            await discover_devices(collector, logger)
            return
        
        elif arg == '--collect-once':
            db_manager = DatabaseManager(config=config)
            await collect_once(collector, db_manager, logger)
            return
        
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("\nUsage:")
            print("  python amazon_alexa_collector_main.py --discover       # List all devices")
            print("  python amazon_alexa_collector_main.py --collect-once   # Single collection")
            print("  python amazon_alexa_collector_main.py                  # Continuous mode")
            sys.exit(1)
    
    # Production mode: continuous collection
    db_manager = DatabaseManager(config=config)
    
    # Get collection interval from config
    amazon_config = config.get('amazon_aqm', {})
    interval = amazon_config.get('collection_interval', 300)
    
    try:
        await collect_continuous(collector, db_manager, logger, interval)
    except KeyboardInterrupt:
        logger.info("Collector stopped by user")
    except Exception as e:
        logger.error(f"Collector crashed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
