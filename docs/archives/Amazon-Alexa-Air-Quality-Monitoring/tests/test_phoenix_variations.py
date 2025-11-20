#!/usr/bin/env python3
"""
Test script - try different variations of the phoenix endpoint.
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
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json',
})

for name, value in cookies.items():
    session.cookies.set(name, value, domain='.amazon.com')

# Try different variations
endpoints = [
    ("GET /api/phoenix", "https://alexa.amazon.com/api/phoenix", {}),
    ("POST /api/phoenix", "https://alexa.amazon.com/api/phoenix", {"method": "POST"}),
    ("GET /api/phoenix/state", "https://alexa.amazon.com/api/phoenix/state", {}),
    ("GET /api/behaviors/entities?skillId=amzn1.ask.1p.smarthome", "https://alexa.amazon.com/api/behaviors/entities?skillId=amzn1.ask.1p.smarthome", {}),
]

for name, url, opts in endpoints:
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print('='*60)
    try:
        if opts.get("method") == "POST":
            response = session.post(url, timeout=10)
        else:
            response = session.get(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Got JSON response!")
                print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                
                filename = f"debug_{name.replace('/', '_').replace(' ', '_')}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Saved to: {filename}")
                
                # Search for air quality
                response_str = json.dumps(data).lower()
                if 'air' in response_str or 'quality' in response_str:
                    print("⭐ Contains 'air' or 'quality'!")
            except:
                print(f"Not JSON: {response.text[:200]}")
        else:
            print(f"Status {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"Exception: {e}")
