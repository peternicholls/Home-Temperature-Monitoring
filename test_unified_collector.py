#!/usr/bin/env python3
"""Quick test of unified Amazon/Alexa collector"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from source.collectors.amazon_unified_collector import AmazonUnifiedCollector
from source.config.loader import load_config, load_secrets
from source.utils.structured_logger import StructuredLogger


async def test_discovery():
    """Test device discovery"""
    
    # Load config and secrets
    config = load_config()
    secrets = load_secrets()
    config['component'] = 'test_unified'
    
    # IMPORTANT: Copy collectors.amazon_aqm to top level (same as working main scripts)
    if 'collectors' in config and 'amazon_aqm' in config['collectors']:
        config['amazon_aqm'] = config['collectors']['amazon_aqm']
    
    logger = StructuredLogger(config)
    cookies = secrets.get('amazon_aqm', {}).get('cookies', {})
    
    if not cookies:
        print("❌ No cookies found in secrets.yaml")
        return False
    
    print("=" * 80)
    print("TESTING UNIFIED AMAZON/ALEXA COLLECTOR")
    print("=" * 80)
    print()
    
    # Create collector
    collector = AmazonUnifiedCollector(cookies, config, logger)
    
    # Discover devices
    print("🔍 Discovering ALL Amazon/Alexa devices...")
    devices = await collector.list_devices()
    
    if not devices:
        print("❌ No devices found")
        return False
    
    print(f"\n✅ Found {len(devices)} device(s):\n")
    
    for device in devices:
        dtype = device['device_type']
        print(f"  • {device['friendly_name']}")
        print(f"    Type: {dtype}")
        print(f"    ID: {device['device_id']}")
        
        if dtype == 'alexa_aqm':
            print(f"    Serial: {device['device_serial']}")
            print(f"    Entity ID: {device['entity_id']}")
        elif dtype == 'nest_thermostat':
            print(f"    Manufacturer: {device['manufacturer']}")
            print(f"    Model: {device['model_name']}")
        
        print()
    
    print("=" * 80)
    return True


if __name__ == '__main__':
    success = asyncio.run(test_discovery())
    sys.exit(0 if success else 1)
