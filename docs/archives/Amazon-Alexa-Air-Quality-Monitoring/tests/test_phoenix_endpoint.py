#!/usr/bin/env python3
"""
Test script to find Amazon Air Quality Monitor using the correct endpoint.
Based on Home Assistant's Alexa Media Player integration.
"""
import sys
import os
import yaml
import requests
import json

# Load secrets
with open('config/secrets.yaml', 'r') as f:
    secrets = yaml.safe_load(f)

cookies = secrets.get('amazon_aqm', {}).get('cookies', {})
print(f"Loaded {len(cookies)} cookies\n")

# Create session
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.9',
})

for name, value in cookies.items():
    session.cookies.set(name, value, domain='.amazon.com')

# The key endpoint from Home Assistant code
print("="*60)
print("Testing: /api/phoenix (network details)")
print("="*60)

url = "https://alexa.amazon.com/api/phoenix"
try:
    response = session.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        # Try to parse as JSON
        try:
            data = response.json()
            print(f"Response type: {type(data)}")
            
            # Save to file
            with open('debug_phoenix_network.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved to: debug_phoenix_network.json")
            
            # Look for network details
            if isinstance(data, dict) and 'networkDetail' in data:
                network_detail = data['networkDetail']
                print(f"\nFound networkDetail with {len(network_detail)} items")
                
                # Look for Air Quality Monitor
                for appliance in network_detail:
                    friendly_desc = appliance.get('friendlyDescription', '')
                    appliance_types = appliance.get('applianceTypes', [])
                    friendly_name = appliance.get('friendlyName', '')
                    
                    if 'Air Quality' in friendly_desc or 'AIR_QUALITY_MONITOR' in appliance_types:
                        print(f"\n⭐ FOUND AIR QUALITY MONITOR!")
                        print(f"  Name: {friendly_name}")
                        print(f"  Description: {friendly_desc}")
                        print(f"  Types: {appliance_types}")
                        print(f"  Entity ID: {appliance.get('entityId')}")
                        print(f"  Appliance ID: {appliance.get('applianceId')}")
                        
                        # Save just this device
                        with open('air_quality_monitor_details.json', 'w') as f:
                            json.dump(appliance, f, indent=2)
                        print(f"  Saved details to: air_quality_monitor_details.json")
        except json.JSONDecodeError:
            print(f"Response is not JSON")
            print(f"First 500 chars: {response.text[:500]}")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")
