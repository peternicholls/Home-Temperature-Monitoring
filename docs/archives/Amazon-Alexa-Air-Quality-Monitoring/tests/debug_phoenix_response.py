#!/usr/bin/env python3
"""
Debug script to see what the phoenix API actually returns.
"""
import sys
import os
import yaml
import requests

# Load secrets
with open('../config/secrets.yaml', 'r') as f:
    secrets = yaml.safe_load(f)

cookies = secrets.get('amazon_aqm', {}).get('cookies', {})

# Create session
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
})

for name, value in cookies.items():
    session.cookies.set(name, value, domain='.amazon.com')

# Try the phoenix endpoint
url = "https://alexa.amazon.com/api/phoenix"
print(f"Testing: {url}")
print("="*60)

response = session.get(url, timeout=30)
print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"\nResponse Length: {len(response.text)} bytes")
print(f"Content-Type: {response.headers.get('Content-Type')}")

# Try to parse as JSON
try:
    data = response.json()
    print(f"\n✅ Valid JSON!")
    print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
    
    if isinstance(data, dict) and 'networkDetail' in data:
        print(f"Network Detail Items: {len(data['networkDetail'])}")
except Exception as e:
    print(f"\n❌ Not JSON: {e}")
    print(f"First 500 chars: {response.text[:500]}")
