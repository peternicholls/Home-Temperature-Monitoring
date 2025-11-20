# Amazon AQM Integration Research Artifacts

This directory contains research and debugging scripts used during the development of the Amazon Air Quality Monitor integration.

## Purpose

These files document the exploration process to understand Amazon's Alexa API for retrieving air quality sensor data.

## Key Findings

### Working Components
- **GraphQL Device Discovery**: `/nexus/v1/graphql` successfully returns device list including AQM
- **Cookie Authentication**: Playwright-based cookie capture works correctly
- **Device Metadata**: Can retrieve entity ID, appliance ID, and capability definitions

### Challenges Encountered
- **Phoenix State API**: `/api/phoenix/state` POST endpoint doesn't recognize AQM entity/appliance IDs
- **Compression**: Responses use gzip or zstandard compression
- **State Retrieval**: Current sensor values (temperature, humidity, PM2.5, VOC, CO2) not accessible via standard endpoints

## File Categories

### Device Discovery
- `test_amazon_real_world.py` - End-to-end integration test
- `debug_find_aqm.py` - Device discovery debugging
- `graphql_full_response.json` - Complete device list from GraphQL

### State API Exploration
- `test_phoenix_state_*.py` - Various attempts to retrieve sensor state
- `test_devicestates_*.py` - Testing devicestates endpoint with compression
- `find_state_endpoint.py` - Systematic endpoint discovery

### GraphQL Investigation
- `test_graphql_*.py` - GraphQL introspection and queries
- `test_endpoint_extended.py` - Extended field queries
- `test_interfaces.py` - Interface schema exploration

### API Endpoint Testing
- `test_various_endpoints.py` - Testing multiple API endpoints
- `debug_phoenix_api.py` - Phoenix API debugging

### Response Data
- `*.json` - Captured API responses for analysis

## Current Status

The integration can successfully:
1. Authenticate via cookies
2. Discover the Air Quality Monitor device
3. Retrieve device metadata and capabilities

**Still investigating**: How to retrieve current sensor values. The standard Phoenix state API doesn't work with AQM devices. May require:
- Different API endpoint specific to AQM
- WebSocket/SSE subscription for real-time data
- Alternative approach through Home Assistant integration

## Next Steps

1. Investigate Home Assistant's Alexa Media Player integration source code
2. Monitor network traffic from Alexa mobile app when viewing AQM
3. Check if AQM data is available through different Amazon service endpoint
4. Consider alternative: Use Home Assistant as intermediary

## Reference Documentation

- [Home Assistant Alexa Media Player](https://github.com/custom-components/alexa_media_player)
- [Amazon Alexa Smart Home API](https://developer.amazon.com/en-US/docs/alexa/smarthome/understand-connections.html)
- Main implementation: `source/collectors/amazon_collector.py`
- Authentication: `source/collectors/amazon_auth.py`
