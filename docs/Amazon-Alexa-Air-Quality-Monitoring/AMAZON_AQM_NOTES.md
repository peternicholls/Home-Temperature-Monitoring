# Amazon Air Quality Monitor - Device Information

## Network Details
- **Hostname**: AmazonAQM-00H3
- **IP Address**: 192.168.1.62
- **MAC Address**: B0:CF:CB:DC:72:72
- **Last Seen**: 22:01:28

## Current Status

### ✅ What's Working
1. **Authentication**: Successfully captured 17 Amazon cookies
2. **API Access**: Can authenticate with Amazon Alexa API
3. **Device Confirmed**: Device is on local network and registered

### ❌ Current Challenge
The Amazon Smart Air Quality Monitor does **not appear** in the standard Alexa device API endpoints:
- `/api/devices-v2/device` - Returns only Echo devices and TVs
- `/api/phoenix/group` - Returns empty appliance groups
- `/api/phoenix/state` - Returns empty response

## Why This Happens

According to research and Amazon's documentation:
1. **No Public API**: Amazon does not provide a public API for accessing Air Quality Monitor data
2. **Alexa App Only**: Data is designed to be viewed only in the Alexa app or on Echo Show devices
3. **Different Category**: The Air Quality Monitor may be categorized as an environmental sensor rather than a standard Alexa device

## Potential Solutions

### Option 1: Unofficial Alexa API (Current Approach)
- **Status**: Partially implemented
- **Challenge**: Need to find the correct endpoint that lists the Air Quality Monitor
- **Next Steps**: 
  - Inspect Alexa app network traffic to find the actual endpoint
  - Look for endpoints specific to environmental sensors or smart home appliances
  - Try endpoints with the device serial/MAC address

### Option 2: Local Network Polling
- **Status**: Not feasible
- **Reason**: Device at 192.168.1.62 doesn't expose HTTP API
- **Finding**: Port 80 refused, device blocks ping probes

### Option 3: Alexa Skills Kit
- **Status**: Not explored
- **Approach**: Create a custom Alexa skill that can query device state
- **Complexity**: High - requires skill development and certification

### Option 4: Home Assistant Integration
- **Status**: Not explored
- **Approach**: Use Home Assistant's Amazon integration if available
- **Benefit**: Community-maintained, may have solved this problem

### Option 5: Manual Data Entry
- **Status**: Fallback option
- **Approach**: Manually check Alexa app and enter data
- **Benefit**: Simple, guaranteed to work
- **Drawback**: Not automated

## Recommended Next Steps

1. **Inspect Alexa App Traffic**
   - Open Alexa app on phone/computer
   - Use browser dev tools or proxy (Charles, mitmproxy)
   - Navigate to Air Quality Monitor page
   - Capture the API endpoint used to fetch data

2. **Search for Appliance ID**
   - The device likely has an "appliance ID" starting with "AAA_SonarCloudService_"
   - This ID might be in a different API endpoint we haven't tried yet

3. **Try Entity-Based Endpoints**
   - Look for endpoints that use entity IDs rather than device IDs
   - Environmental sensors might be under a different category

4. **Community Research**
   - Check Home Assistant forums for Amazon AQM integration
   - Look for existing Python libraries that access this data

## Files for Reference
- Network info: This file
- API exploration: `debug_amazon_api.py`, `debug_extended_api.py`
- Saved API responses: `debug_device.json`, `debug_group.json`

## Configuration
The collector is ready and waiting - once we find the correct API endpoint, updating `source/collectors/amazon_collector.py` will be straightforward.
