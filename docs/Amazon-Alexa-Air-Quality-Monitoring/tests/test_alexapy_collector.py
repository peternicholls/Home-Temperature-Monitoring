#!/usr/bin/env python3
"""
Test script for the updated Amazon AQM collector using alexapy.
"""
import sys
import os
import yaml
import logging

# Add source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from collectors.amazon_collector import AmazonAQMCollector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load config and secrets
with open('../config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

with open('../config/secrets.yaml', 'r') as f:
    secrets = yaml.safe_load(f)

print("="*60)
print("Testing Amazon AQM Collector with alexapy")
print("="*60)
print(f"\nCookies loaded: {len(secrets.get('amazon_aqm', {}).get('cookies', {}))} cookies")

# Create collector
collector = AmazonAQMCollector(config, secrets)

print("\n" + "="*60)
print("Collecting data...")
print("="*60)

# Collect data
data = collector.collect()

print("\n" + "="*60)
print("Results:")
print("="*60)

if data:
    print(f"\n✅ Successfully collected {len(data)} metrics:")
    for key, value in data.items():
        print(f"  {key}: {value}")
else:
    print("\n❌ No data collected")

print("\n" + "="*60)
