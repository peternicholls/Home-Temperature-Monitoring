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
import yaml
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from source.collectors.amazon_collector import AmazonAQMCollector
from source.collectors.amazon_auth import validate_amazon_cookies, check_cookie_expiration
from source.storage.manager import DatabaseManager
from source.config.loader import load_config
from source.utils.structured_logger import StructuredLogger

# Configure structured logging with fixed component name
logger: Optional[StructuredLogger] = None  # Will be initialized in main() with config


async def discover_devices(cookies: dict, config: dict):
    """
    List all Amazon AQM devices.
    
    Args:
        cookies: Amazon authentication cookies
        config: Configuration dictionary
    """
    try:
        start_time = time.time()
        collector = AmazonAQMCollector(cookies, config, logger)
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
            return
        
        device_ids = [d.get('device_id', 'unknown') for d in devices]
        
        if logger:
            logger.success(
                "Device discovery complete",
                device_count=len(devices),
                device_ids=device_ids,
                discovery_duration_ms=discovery_duration_ms
            )
        
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
    Collect data once and store in database.
    
    Args:
        cookies: Amazon authentication cookies
        config: Configuration dictionary
        db_manager: DatabaseManager instance
    """
    try:
        start_time = time.time()
        collector = AmazonAQMCollector(cookies, config, logger)
        success = await collector.collect_and_store(db_manager)
        cycle_duration_ms = int((time.time() - start_time) * 1000)
        
        if success:
            if logger:
                logger.success(
                    "Collection completed successfully",
                    cycle_duration_ms=cycle_duration_ms,
                    status="success"
                )
        else:
            if logger:
                logger.warning(
                    "Collection completed with no new data",
                    cycle_duration_ms=cycle_duration_ms,
                    status="partial"
                )
        
    except Exception as e:
        if logger:
            logger.error(
                f"Collection failed: {e}",
                error_code="COLLECTION_FAILED",
                error_message=str(e),
                exc_info=True
            )


async def collect_continuous(cookies: dict, config: dict, db_manager: DatabaseManager):
    """
    Continuous collection loop.
    
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
        logger.info(f"Starting continuous collection, interval {collection_interval}s")
    
    cycle_count = 0
    total_errors = 0
    
    try:
        while True:
            cycle_count += 1
            cycle_start = time.time()
            
            if logger:
                logger.info(f"\n--- Collection Cycle {cycle_count} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
            
            # Attempt collection with retries
            success = False
            for attempt in range(1, retry_attempts + 1):
                try:
                    collector = AmazonAQMCollector(cookies, config, logger)
                    success = await collector.collect_and_store(db_manager)
                    
                    if success:
                        cycle_duration_ms = int((time.time() - cycle_start) * 1000)
                        if logger:
                            logger.info(
                                f"Cycle {cycle_count} complete - readings stored",
                                cycle_number=cycle_count,
                                cycle_duration_ms=cycle_duration_ms,
                                attempt_number=attempt,
                                status="success"
                            )
                        break
                    else:
                        if logger:
                            logger.warning(
                                f"Cycle {cycle_count} - no new data (attempt {attempt}/{retry_attempts})",
                                cycle_number=cycle_count,
                                attempt_number=attempt,
                                status="no_data"
                            )
                        
                        if attempt < retry_attempts:
                            wait_time = retry_backoff_base * (2 ** (attempt - 1))
                            if logger:
                                logger.info(f"Retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                
                except Exception as e:
                    total_errors += 1
                    if logger:
                        logger.error(
                            f"Error in collection attempt {attempt}: {e}",
                            cycle_number=cycle_count,
                            attempt_number=attempt,
                            error_code="COLLECTION_ATTEMPT_FAILED",
                            error_message=str(e)
                        )
                    
                    if attempt < retry_attempts:
                        wait_time = retry_backoff_base * (2 ** (attempt - 1))
                        if logger:
                            logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        if logger:
                            logger.error(
                                f"Cycle {cycle_count} failed after {retry_attempts} attempts",
                                cycle_number=cycle_count,
                                max_attempts=retry_attempts,
                                status="failed"
                            )
            
            # Calculate time until next collection
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, collection_interval - cycle_duration)
            
            if sleep_time > 0:
                next_collection = datetime.fromtimestamp(time.time() + sleep_time)
                if logger:
                    logger.info(f"Next collection at {next_collection.strftime('%H:%M:%S')} (in {sleep_time:.0f}s)")
                await asyncio.sleep(sleep_time)
            else:
                if logger:
                    logger.warning(
                        f"Collection took {cycle_duration:.1f}s (exceeds interval of {collection_interval}s)",
                        cycle_duration_ms=int(cycle_duration * 1000),
                        interval_seconds=collection_interval
                    )
    
    except KeyboardInterrupt:
        if logger:
            logger.warning(
                "Continuous collection stopped by user",
                cycles_completed=cycle_count,
                total_errors=total_errors,
                final_timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            logger.info(f"Total cycles completed: {cycle_count}")


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
        print(f"ERROR: Failed to load config from {args.config}: {e}")
        sys.exit(1)
    
    # Initialize logger with config
    config['component'] = 'amazon_aqm_collector'
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
        logger.warning(
            "Cookie expiration warning",
            is_expired=True,
            warning_message=warning
        )
    
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
