#!/usr/bin/env python3
"""
Amazon Air Quality Monitor Collector - Main Script

Standalone script for AQM collection with multiple operation modes.
Mirrors the structure of hue_collector.py for consistency.

Usage:
    python source/collectors/amazon_aqm_collector_main.py --discover
    python source/collectors/amazon_aqm_collector_main.py --collect-once
    python source/collectors/amazon_aqm_collector_main.py --continuous
"""

import asyncio
import argparse
import logging
import yaml
import time
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from source.collectors.amazon_collector import AmazonAQMCollector
from source.collectors.amazon_auth import validate_amazon_cookies, check_cookie_expiration
from source.storage.manager import DatabaseManager
from source.config.loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def discover_devices(cookies: dict, config: dict):
    """
    List all Amazon AQM devices.
    
    Args:
        cookies: Amazon authentication cookies
        config: Configuration dictionary
    """
    logger.info("=" * 80)
    logger.info("Device Discovery Mode")
    logger.info("=" * 80)
    
    try:
        collector = AmazonAQMCollector(cookies, config)
        devices = await collector.list_devices()
        
        if not devices:
            logger.warning("No Amazon Air Quality Monitors found")
            logger.info("\nPossible reasons:")
            logger.info("  1. No AQM devices registered to this account")
            logger.info("  2. Cookies are expired (try re-authenticating)")
            logger.info("  3. Device is offline or not connected to WiFi")
            return
        
        logger.info(f"\n✅ Found {len(devices)} device(s):\n")
        
        for i, device in enumerate(devices, 1):
            logger.info(f"Device {i}:")
            logger.info(f"  Device ID:     {device['device_id']}")
            logger.info(f"  Entity ID:     {device['entity_id']}")
            logger.info(f"  Serial Number: {device['device_serial']}")
            logger.info(f"  Name:          {device.get('friendly_name', 'Unknown')}")
            logger.info(f"  Capabilities:  {len(device.get('capabilities', []))} capabilities")
            logger.info("")
        
        logger.info("=" * 80)
        logger.info("Device discovery complete")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during device discovery: {e}", exc_info=True)


async def collect_once(cookies: dict, config: dict, db_manager: DatabaseManager):
    """
    Collect data once and store in database.
    
    Args:
        cookies: Amazon authentication cookies
        config: Configuration dictionary
        db_manager: DatabaseManager instance
    """
    logger.info("=" * 80)
    logger.info("Single Collection Mode")
    logger.info("=" * 80)
    
    try:
        collector = AmazonAQMCollector(cookies, config)
        success = await collector.collect_and_store(db_manager)
        
        if success:
            logger.info("\n✅ Collection successful - readings stored in database")
        else:
            logger.warning("\n⚠️  Collection failed or no new data")
        
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during collection: {e}", exc_info=True)


async def collect_continuous(cookies: dict, config: dict, db_manager: DatabaseManager):
    """
    Continuous collection loop.
    
    Args:
        cookies: Amazon authentication cookies
        config: Configuration dictionary
        db_manager: DatabaseManager instance
    """
    logger.info("=" * 80)
    logger.info("Continuous Collection Mode")
    logger.info("=" * 80)
    
    amazon_config = config.get('amazon_aqm', {})
    collection_interval = amazon_config.get('collection_interval', 300)  # Default 5 minutes
    retry_attempts = amazon_config.get('retry_attempts', 3)
    retry_backoff_base = amazon_config.get('retry_backoff_base', 1.0)
    
    logger.info(f"Collection interval: {collection_interval} seconds ({collection_interval / 60:.1f} minutes)")
    logger.info(f"Retry attempts: {retry_attempts}")
    logger.info(f"Starting continuous collection... (Press Ctrl+C to stop)")
    logger.info("=" * 80)
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            cycle_start = time.time()
            
            logger.info(f"\n--- Collection Cycle {cycle_count} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
            
            # Attempt collection with retries
            success = False
            for attempt in range(1, retry_attempts + 1):
                try:
                    collector = AmazonAQMCollector(cookies, config)
                    success = await collector.collect_and_store(db_manager)
                    
                    if success:
                        logger.info(f"✅ Cycle {cycle_count} complete - readings stored")
                        break
                    else:
                        logger.warning(f"⚠️  Cycle {cycle_count} - no new data (attempt {attempt}/{retry_attempts})")
                        
                        if attempt < retry_attempts:
                            wait_time = retry_backoff_base * (2 ** (attempt - 1))
                            logger.info(f"Retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                
                except Exception as e:
                    logger.error(f"Error in collection attempt {attempt}: {e}")
                    
                    if attempt < retry_attempts:
                        wait_time = retry_backoff_base * (2 ** (attempt - 1))
                        logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"❌ Cycle {cycle_count} failed after {retry_attempts} attempts")
            
            # Calculate time until next collection
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, collection_interval - cycle_duration)
            
            if sleep_time > 0:
                next_collection = datetime.fromtimestamp(time.time() + sleep_time)
                logger.info(f"Next collection at {next_collection.strftime('%H:%M:%S')} (in {sleep_time:.0f}s)")
                await asyncio.sleep(sleep_time)
            else:
                logger.warning(f"Collection took {cycle_duration:.1f}s (exceeds interval of {collection_interval}s)")
    
    except KeyboardInterrupt:
        logger.info("\n\n" + "=" * 80)
        logger.info("Continuous collection stopped by user")
        logger.info(f"Total cycles completed: {cycle_count}")
        logger.info("=" * 80)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Amazon Air Quality Monitor Collector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Discover devices:
    python source/collectors/amazon_aqm_collector_main.py --discover
  
  Single collection:
    python source/collectors/amazon_aqm_collector_main.py --collect-once
  
  Continuous collection:
    python source/collectors/amazon_aqm_collector_main.py --continuous
        """
    )
    
    parser.add_argument('--discover', action='store_true', help='List all AQM devices')
    parser.add_argument('--collect-once', action='store_true', help='Collect data once')
    parser.add_argument('--continuous', action='store_true', help='Continuous collection loop')
    parser.add_argument('--config', default='config/config.yaml', help='Path to config file')
    parser.add_argument('--secrets', default='config/secrets.yaml', help='Path to secrets file')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not (args.discover or args.collect_once or args.continuous):
        parser.print_help()
        print("\n❌ Error: Must specify one of: --discover, --collect-once, or --continuous")
        sys.exit(1)
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {args.config}: {e}")
        sys.exit(1)
    
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
        logger.error("\n❌ Cookie validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("\nPlease re-authenticate using the web UI:")
        logger.error("  1. Run: python source/web/app.py")
        logger.error("  2. Navigate to: http://localhost:5001/setup")
        logger.error("  3. Click 'Connect Amazon Account' and log in")
        sys.exit(1)
    
    # Check cookie expiration
    is_expired, warning = check_cookie_expiration(cookies)
    if is_expired:
        logger.warning(f"\n⚠️  {warning}")
        logger.warning("Consider re-authenticating soon to avoid collection failures\n")
    
    # Normalize config structure - move collectors.amazon_aqm to amazon_aqm
    if 'collectors' in config and 'amazon_aqm' in config['collectors']:
        config['amazon_aqm'] = config['collectors']['amazon_aqm']
        logger.debug("Normalized config: moved collectors.amazon_aqm to amazon_aqm")
    
    # Execute requested mode
    if args.discover:
        await discover_devices(cookies, config)
    
    elif args.collect_once:
        db_manager = DatabaseManager(config=config)
        await collect_once(cookies, config, db_manager)
        db_manager.close()
    
    elif args.continuous:
        db_manager = DatabaseManager(config=config)
        await collect_continuous(cookies, config, db_manager)
        db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
