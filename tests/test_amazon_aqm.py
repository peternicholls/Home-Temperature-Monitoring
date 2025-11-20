#!/usr/bin/env python3
"""
Test the updated amazon_collector.py with correct endpoint
"""
import sys
import asyncio
import yaml
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from source.collectors.amazon_collector import AmazonAQMCollector

async def main():
    print("=" * 80)
    print("Testing Updated AmazonAQMCollector")
    print("=" * 80)
    
    # Load cookies and config
    with open("config/secrets.yaml") as f:
        secrets = yaml.safe_load(f)
    cookies = secrets['amazon_aqm']['cookies']
    
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)
    
    # Add Amazon AQM config
    config['amazon_aqm'] = {
        'domain': 'alexa.amazon.co.uk',  # UK domain
        'device_serial': 'GAJ23005314600H3'
    }
    
    # Create collector
    collector = AmazonAQMCollector(cookies, config)
    
    # Test device discovery
    print("\n1. Device Discovery")
    print("-" * 80)
    devices = await collector.list_devices()
    print(f"Found {len(devices)} devices")
    
    if devices:
        device = devices[0]
        print(f"\nFirst device keys: {list(device.keys())}")
        print(f"  Name: {device.get('device_name', 'N/A')}")
        print(f"  Entity ID: {device.get('entity_id', 'N/A')}")
        print(f"  Serial: {device.get('device_serial', 'N/A')}")
        
        # Test get readings
        print("\n2. Get Air Quality Readings")
        print("-" * 80)
        readings = await collector.get_air_quality_readings(device['entity_id'])
        
        if readings:
            print(f"✅ SUCCESS! Collected {len(readings) - 1} readings:")
            for key, value in readings.items():
                if key != 'timestamp':
                    print(f"  {key}: {value}")
            
            # Validate
            print("\n3. Validation")
            print("-" * 80)
            errors = collector.validate_readings(readings)
            if errors:
                print(f"❌ Validation errors:")
                for error in errors:
                    print(f"  - {error}")
            else:
                print(f"✅ All readings valid!")
        else:
            print("❌ Failed to get readings")
    else:
        print("❌ No devices found")

if __name__ == "__main__":
    asyncio.run(main())
