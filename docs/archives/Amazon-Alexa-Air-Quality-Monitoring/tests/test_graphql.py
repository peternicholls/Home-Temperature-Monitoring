#!/usr/bin/env python3
"""
Test the GraphQL endpoint with cookies and CSRF token.
"""
import sys
import os
import yaml
import requests
import json

# Load secrets
with open('../config/secrets.yaml', 'r') as f:
    secrets = yaml.safe_load(f)

cookies_dict = secrets.get('amazon_aqm', {}).get('cookies', {})
csrf_token = cookies_dict.get('csrf', '')

print(f"Loaded {len(cookies_dict)} cookies")
print(f"CSRF token: {csrf_token[:20]}..." if csrf_token else "No CSRF token")

# Create session
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://alexa.amazon.com/spa/index.html',
    'csrf': csrf_token,
})

for name, value in cookies_dict.items():
    session.cookies.set(name, value, domain='.amazon.com')

# GraphQL query
query = """
query CustomerSmartHome {
    endpoints(
        endpointsQueryParams: { paginationParams: { disablePagination: true } }
    ) {
        items {
            legacyAppliance {
                applianceId
                applianceTypes
                friendlyName
                friendlyDescription
                entityId
                capabilities
            }
        }
   }
}
"""

url = "https://alexa.amazon.co.uk/nexus/v1/graphql"
print(f"\nTesting: {url}")
print("="*60)

response = session.post(url, json={"query": query}, timeout=30)
print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")

try:
    data = response.json()
    print(f"\n✅ Got JSON response!")
    
    # Save to file
    with open('graphql_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved to: graphql_response.json")
    
    # Check for errors
    if 'errors' in data:
        print(f"\n❌ GraphQL Errors:")
        for error in data['errors']:
            print(f"  - {error.get('message', error)}")
    
    # Check for data
    if 'data' in data:
        endpoints = data.get('data', {}).get('endpoints', {}).get('items', [])
        print(f"\n✅ Found {len(endpoints)} endpoints")
        
        if endpoints:
            for i, endpoint in enumerate(endpoints[:3]):
                appliance = endpoint.get('legacyAppliance', {})
                print(f"\nEndpoint {i+1}:")
                print(f"  Name: {appliance.get('friendlyName')}")
                print(f"  Types: {appliance.get('applianceTypes', [])}")
        else:
            print(f"  (endpoints list is empty)")
            print(f"  Full data structure keys: {list(data.keys())}")
            
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Response: {response.text[:1000]}")
