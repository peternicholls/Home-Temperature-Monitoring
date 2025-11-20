#!/usr/bin/env python3
"""
Quick test script to verify Amazon AQM collector works with saved cookies.
"""
import sys
import os
import yaml

# Add source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'source'))

from source.collectors.amazon_collector import AmazonAQMCollector

# Load config and secrets
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

with open('config/secrets.yaml', 'r') as f:
    secrets = yaml.safe_load(f)

print("Testing Amazon AQM Collector...")
print(f"Cookies loaded: {len(secrets.get('amazon_aqm', {}).get('cookies', {}))} cookies")

collector = AmazonAQMCollector(config, secrets)

print("\nDiscovering devices...")
devices = collector.discover_devices()
print(f"Found {len(devices)} device(s)")

if devices:
    for i, device in enumerate(devices):
        print(f"\nDevice {i+1}:")
        print(f"  Serial: {device.get('serialNumber')}")
        print(f"  Name: {device.get('accountName')}")
        print(f"  Type: {device.get('deviceType')}")

print("\nAttempting to collect data...")
data = collector.collect()
print(f"Collected data: {data}")
