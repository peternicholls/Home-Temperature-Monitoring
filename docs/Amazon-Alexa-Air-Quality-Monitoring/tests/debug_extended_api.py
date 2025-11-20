#!/usr/bin/env python3
"""
Extended API exploration for Amazon Air Quality Monitor.
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

# Try more endpoints that might have smart home devices
endpoints = [
    "https://alexa.amazon.com/api/behaviors/entities",
    "https://alexa.amazon.com/api/entities",
    "https://alexa.amazon.com/api/phoenix",
    "https://alexa.amazon.com/api/behaviors/v2/automations",
    "https://alexa.amazon.com/api/phoenix/appliance",
    "https://alexa.amazon.com/api/eon/entity-state",
]

for endpoint in endpoints:
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint}")
    print('='*60)
    try:
        response = session.get(endpoint, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Response keys: {list(data.keys())[:10]}")
                elif isinstance(data, list):
                    print(f"Response list length: {len(data)}")
                
                # Save to file for inspection
                filename = f"debug_{endpoint.split('/')[-1]}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Saved full response to: {filename}")
                
                # Search for air quality related terms
                response_str = json.dumps(data).lower()
                if any(term in response_str for term in ['air', 'quality', 'monitor', 'sonar', '00h3']):
                    print("⭐ FOUND AIR QUALITY RELATED DATA!")
            except:
                print(f"Response (not JSON): {response.text[:200]}")
        else:
            print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
