"""
Hue API Optimization - Sensors-Only Endpoint

Before: bridge.get_api() fetches entire bridge configuration (~180KB)
After: Direct HTTP request to /api/<key>/sensors (~8KB)

Expected improvements:
- 95%+ reduction in response payload size
- 30%+ reduction in collection cycle time
- Lower JSON parsing overhead
- Same sensor data structure (backward compatible)
"""

import requests
import time
import sys
from datetime import datetime


def fetch_full_config_old_way(bridge_ip: str, api_key: str) -> dict:
    """
    OLD WAY: Fetch full bridge configuration.
    
    Returns entire bridge state including:
    - All lights and their states
    - Groups and scenes
    - Schedules and rules
    - Configuration settings
    - Sensors
    - Resource links
    """
    url = f"http://{bridge_ip}/api/{api_key}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    return data


def fetch_sensors_only_new_way(bridge_ip: str, api_key: str) -> dict:
    """
    NEW WAY: Fetch only sensor data.
    
    Returns only sensors section, much smaller payload.
    """
    url = f"http://{bridge_ip}/api/{api_key}/sensors"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    return data


def compare_approaches(bridge_ip: str, api_key: str):
    """
    Compare old (full config) vs new (sensors only) approaches.
    
    Measures:
    - Response payload size
    - Request duration
    - Sensor count (should be identical)
    """
    print("=" * 70)
    print("HUE API OPTIMIZATION COMPARISON")
    print("=" * 70)
    print()
    
    # Test OLD WAY
    print("📊 OLD WAY: Fetching full bridge configuration...")
    start = time.time()
    full_config = fetch_full_config_old_way(bridge_ip, api_key)
    old_duration_ms = int((time.time() - start) * 1000)
    
    old_size_bytes = sys.getsizeof(str(full_config))
    old_sensors = full_config.get('sensors', {})
    old_sensor_count = len([s for s in old_sensors.values() if s.get('type') == 'ZLLTemperature'])
    
    print(f"   Size: {old_size_bytes:,} bytes ({old_size_bytes / 1024:.1f} KB)")
    print(f"   Duration: {old_duration_ms} ms")
    print(f"   Temperature sensors: {old_sensor_count}")
    print()
    
    # Test NEW WAY
    print("📊 NEW WAY: Fetching sensors only...")
    start = time.time()
    sensors_only = fetch_sensors_only_new_way(bridge_ip, api_key)
    new_duration_ms = int((time.time() - start) * 1000)
    
    new_size_bytes = sys.getsizeof(str(sensors_only))
    new_sensor_count = len([s for s in sensors_only.values() if s.get('type') == 'ZLLTemperature'])
    
    print(f"   Size: {new_size_bytes:,} bytes ({new_size_bytes / 1024:.1f} KB)")
    print(f"   Duration: {new_duration_ms} ms")
    print(f"   Temperature sensors: {new_sensor_count}")
    print()
    
    # Calculate improvements
    size_reduction_pct = ((old_size_bytes - new_size_bytes) / old_size_bytes) * 100
    speed_improvement_pct = ((old_duration_ms - new_duration_ms) / old_duration_ms) * 100
    
    print("=" * 70)
    print("📈 IMPROVEMENT METRICS")
    print("=" * 70)
    print(f"✅ Payload size reduction: {size_reduction_pct:.1f}%")
    print(f"✅ Speed improvement: {speed_improvement_pct:.1f}%")
    print(f"✅ Sensor count match: {old_sensor_count == new_sensor_count}")
    print()
    
    # Verify data structure compatibility
    print("🔍 DATA STRUCTURE COMPATIBILITY")
    print("=" * 70)
    
    # Compare sensor data structure
    if old_sensors and sensors_only:
        sample_old_id = list(old_sensors.keys())[0]
        sample_new_id = list(sensors_only.keys())[0]
        
        old_sensor = old_sensors[sample_old_id]
        new_sensor = sensors_only[sample_new_id]
        
        # Check if keys are identical
        old_keys = set(old_sensor.keys())
        new_keys = set(new_sensor.keys())
        
        if old_keys == new_keys:
            print("✅ Sensor data structure IDENTICAL (backward compatible)")
        else:
            print("⚠️  Sensor data structure DIFFERENT")
            print(f"   Keys in old but not new: {old_keys - new_keys}")
            print(f"   Keys in new but not old: {new_keys - old_keys}")
    
    print()
    
    # Success criteria check
    print("=" * 70)
    print("SUCCESS CRITERIA VALIDATION")
    print("=" * 70)
    
    if size_reduction_pct >= 50:
        print(f"✅ PASS: Payload reduction >= 50% (actual: {size_reduction_pct:.1f}%)")
    else:
        print(f"❌ FAIL: Payload reduction < 50% (actual: {size_reduction_pct:.1f}%)")
    
    if speed_improvement_pct >= 30:
        print(f"✅ PASS: Speed improvement >= 30% (actual: {speed_improvement_pct:.1f}%)")
    else:
        print(f"⚠️  MARGINAL: Speed improvement < 30% (actual: {speed_improvement_pct:.1f}%)")
        print("   Note: Absolute time savings may still be valuable")
    
    if old_sensor_count == new_sensor_count:
        print(f"✅ PASS: Sensor count matches ({old_sensor_count} sensors)")
    else:
        print(f"❌ FAIL: Sensor count mismatch (old={old_sensor_count}, new={new_sensor_count})")
    
    print("=" * 70)


# Example usage with actual bridge credentials
if __name__ == '__main__':
    # USAGE: Replace with your actual bridge IP and API key
    # bridge_ip = "192.168.1.105"
    # api_key = "your_api_key_here"
    # compare_approaches(bridge_ip, api_key)
    
    print("This is a reference implementation.")
    print("Update bridge_ip and api_key variables to run actual comparison.")
