#!/usr/bin/env python3
"""
Debug script to explore Amazon Alexa API endpoints.
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

# Try different endpoints
endpoints = [
    "https://alexa.amazon.com/api/devices-v2/device",
    "https://alexa.amazon.com/api/phoenix/state",
    "https://alexa.amazon.com/api/phoenix/group",
]

for endpoint in endpoints:
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint}")
    print('='*60)
    try:
        response = session.get(endpoint, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Save to file for inspection
            filename = f"debug_{endpoint.split('/')[-1]}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved full response to: {filename}")
        else:
            print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
