# Amazon Alexa → Nest Thermostat Data Access

**Date**: 21 November 2025  
**Status**: ✅ Working proof-of-concept  
**Method**: Alexa Phoenix State API

## Summary

Successfully retrieved real temperature data from Nest thermostat ("Hallway") via Alexa's GraphQL and Phoenix State APIs. The device ID format from GraphQL doesn't work with Nest's direct API, but Alexa's APIs work fine.

## Device Found

```
Device: Hallway (Nest Thermostat)
Appliance ID: SKILL_eyJza2lsbElkIjoiYW16bjEuYXNrLnNraWxsLjM5YmFhMWQ5LTczMTUtNDAxYi1hNWIzLWRjYzgzOGM2YTg3OCIsInN0YWdlIjoibGl2ZSJ9_QVZQSHdFdlkzTG15MldwOWdzZ2tWaDR5ZkJkaGNhNzBGNFlwZ3haTF9hVEstNGRDbEpaZnVnM2Etam1xa2p1WUhYUklDeXlDWExSX2FsOWg5UXh2WVhYY0tReTE4UQ==
Entity ID: ae766a73-1294-4d29-ac93-1e51fa1ecb63
```

## Data Available

### ✅ Working Data (Retrieved via Phoenix State API)

| Data Point | Value | Unit | Notes |
|------------|-------|------|-------|
| Temperature | 22 | °C | Current room temperature, labeled as `Alexa.TemperatureSensor` |
| Target Setpoint | 21 | °C | Desired temperature, from `Alexa.ThermostatController` |
| Thermostat Mode | HEAT | enum | Modes: HEAT, OFF, ECO |
| Connectivity | OK | string | Device health status |

### 🔑 Key Finding: The Magic Appliance ID

The **correct device ID** for the Phoenix State API is the long `SKILL_...` base64-encoded string from the GraphQL response, NOT the simple entity ID (`ae766a73-1294-4d29-ac93-1e51fa1ecb63`).

```
✅ WORKS:  entityId: "SKILL_eyJza2lsbElkIjoiYW16bjEuYXNrLnNraWxsLjM5YmFhMWQ5LTczMTUtNDAxYi1hNWIzLWRjYzgzOGM2YTg3OCIsInN0YWdlIjoibGl2ZSJ9_QVZQSHdFdlkzTG15MldwOWdzZ2tWaDR5ZkJkaGNhNzBGNFlwZ3haTF9hVEstNGRDbEpaZnVnM2Etam1xa2p1WUhYUklDeXlDWExSX2FsOWg5UXh2WVhYY0tReTE4UQ=="
❌ DOESN'T: entityId: "ae766a73-1294-4d29-ac93-1e51fa1ecb63"
```

The appliance ID is returned in the GraphQL response under `legacyAppliance.applianceId` and must be used in the Phoenix State request.

### ❌ Not Available via Alexa

- **Humidity**: Not exposed by Alexa's API for Nest devices
- **Nest-specific data** (away mode, eco scheduling, energy savings): Restricted by Amazon
- **Raw Nest API access**: Entity ID format is incompatible with Google's SDM API

## API Details

### GraphQL Discovery
- **Endpoint**: `https://alexa.amazon.co.uk/nexus/v1/graphql`
- **Query**: `CustomerSmartHome` query returns all smart home endpoints
- **Returns**: Device metadata including capabilities, appliance ID, entity ID
- **Auth**: Cookie-based (same session cookies as Alexa app)

### Phoenix State API (Polling)
- **Endpoint**: `https://alexa.amazon.co.uk/api/phoenix/state`
- **Method**: POST
- **Payload**:
  ```json
  {
    "stateRequests": [{
      "entityId": "SKILL_...",
      "entityType": "APPLIANCE"
    }]
  }
  ```
- **Response**: JSON with `deviceStates[0].capabilityStates` array
  - Each capability is a JSON string (requires parsing)
  - Includes: `namespace`, `name`, `value`, `timeOfSample`, `uncertaintyInMilliseconds`

### Polling Performance
- Response time: ~1-2 seconds
- Update frequency: ~3-4 second intervals observed
- Rate limiting: No apparent strict limits (tested 5 requests in 10 seconds)
- Reliability: ✅ Stable, no auth errors observed
- **Tested**: 5 rapid requests confirmed consistent updates with fresh timestamps

## Capabilities (GraphQL Response)

```json
{
  "interfaceName": "Alexa.TemperatureSensor",
  "properties": {
    "supported": [{"name": "temperature"}],
    "proactivelyReported": true,
    "retrievable": true,
    "readOnly": false
  }
},
{
  "interfaceName": "Alexa.EndpointHealth",
  "properties": {
    "supported": [{"name": "connectivity"}],
    "proactivelyReported": true,
    "retrievable": true,
    "readOnly": false
  }
},
{
  "interfaceName": "Alexa.ThermostatController",
  "properties": {
    "supported": [
      {"name": "targetSetpoint"},
      {"name": "lowerSetpoint"},
      {"name": "upperSetpoint"},
      {"name": "thermostatMode"}
    ],
    "proactivelyReported": true,
    "retrievable": true,
    "readOnly": false
  },
  "configuration": {
    "supportsScheduling": false,
    "supportedModes": [
      {"value": "HEAT"},
      {"value": "OFF"},
      {"value": "ECO"}
    ],
    "supportsAlexaSensors": false
  }
}
```

## Example Response (Parsed)

```json
{
  "temperature_celsius": 22,
  "target_setpoint_celsius": 21,
  "thermostat_mode": "HEAT",
  "connectivity": "OK",
  "timestamp": "2025-11-21T08:42:18.031949Z"
}
```

## Limitations

1. **Not a replacement for Nest SDK**: Alexa can see the Nest device but doesn't give us deep Nest-specific data
2. **Limited sensor data**: Only temperature + thermostat controls, no humidity or advanced metrics
3. **Dependency on Alexa**: If Amazon restricts or changes this API, our access breaks
4. **No historical data**: Only current state available, not historical readings
5. **Amazon privacy restrictions**: Alexa intentionally restricts Nest data access (privacy reasons)

## Comparison with Direct Nest API

| Feature | Alexa API | Google SDM API |
|---------|-----------|----------------|
| Setup | ✅ Easy (use existing Alexa cookies) | ❌ Requires Google OAuth setup |
| Temperature | ✅ Works | ✅ Works |
| Humidity | ❌ Not exposed | ✅ Available |
| Energy data | ❌ Restricted | ✅ Available |
| Cost | ✅ Free (already have Alexa) | ✅ Free (with OAuth) |
| Stability | ⚠️ Undocumented API | ✅ Official, documented |

## Recommendation

**For Nest thermostat data in Sprint 6:**
- **Short term**: Alexa API works fine for temperature polling (what we've proven here)
- **Long term**: Move to Google SDM API for:
  - Better reliability (official API)
  - More sensor data (humidity, energy, etc.)
  - Cleaner integration (no reverse-engineering required)
  - Support for other Google Nest devices

## Code Reference

Implementation in: `source/collectors/amazon_collector.py`
- Class: `AmazonAQMCollector` (despite name, also handles Nest devices)
- Method: `get_air_quality_readings(entity_id)` - POST to Phoenix State API
- Method: `list_devices()` - GraphQL device discovery

## Next Steps

1. ✅ Verify data accuracy (compare Nest app vs. our readings)
2. ✅ Proof-of-concept confirmed working with correct appliance ID
3. Create collector scheduler for regular polling
4. Store readings in database
5. Create dashboard to visualize thermostat data
6. Plan Google SDM API migration for Sprint 6

## Testing Notes

**Test Date**: 21 November 2025  
**Test Method**: Python async HTTP client with 5 sequential requests (2-second intervals)

**Request 1**: 22°C at 2025-11-21T08:42:46.737474Z  
**Request 2**: 22°C at 2025-11-21T08:42:49.769306Z  
**Request 3**: 22°C at 2025-11-21T08:42:53.458089Z  
**Request 4**: 22°C at 2025-11-21T08:42:57.187831Z  
**Request 5**: 22°C at 2025-11-21T08:43:00.947473Z  

All requests succeeded with consistent data and fresh timestamps. No throttling observed. Response times: 1.0-1.9 seconds.
