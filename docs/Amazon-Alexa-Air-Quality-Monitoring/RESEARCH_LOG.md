# Amazon AQM Data Discovery - Research Log

## Objective
Find the correct API endpoint and method to retrieve real-time sensor data from Amazon Smart Air Quality Monitor.

---

## Session: 2025-11-20

### Iteration 1: Initial Device Discovery
**Status**: ✅ SUCCESS

**What we tried**:
- GraphQL query to `/nexus/v1/graphql` with `CustomerSmartHome` query

**Results**:
- Found 88 devices including "First Air Quality Monitor"
- Retrieved entity ID: `95f34cda-2af4-443b-9b76-40544ea70cba`
- Retrieved appliance ID: `AAA_SonarCloudService_00QAadrq35nr-PZrOPy7y74HsxtQ-bEwPMTOUS_7ZMxqaaH7Tpk4JSoXT_CIyG63-Qu9-0jJX0PF8f5M-0sw`
- Got 10 capabilities:
  - Instance 4: Humidity
  - Instance 5: VOC
  - Instance 6: PM2.5
  - Instance 7: Unknown
  - Instance 8: CO
  - Instance 9: Indoor Air Quality
  - Instance 11: Unknown toggle

**Key Learning**: GraphQL works for device discovery but doesn't include current state/values.

---

### Iteration 2: Phoenix State API - POST with entityId
**Status**: ❌ FAILED

**What we tried**:
- POST to `/api/phoenix/state` with payload:
  ```json
  {"stateRequests": [{"entityId": "95f34cda-2af4-443b-9b76-40544ea70cba", "entityType": "APPLIANCE"}]}
  ```

**Results**:
- HTTP 200 OK (gzip compressed)
- Error response: `"TargetApplianceNotFoundException: No appliance found for target!"`

**Key Learning**: Phoenix state API doesn't recognize the AQM entity ID.

---

### Iteration 3: Phoenix State API - POST with applianceId
**Status**: ❌ FAILED

**What we tried**:
- POST to `/api/phoenix/state` with `applianceId` instead of `entityId`

**Results**:
- HTTP 400 Bad Request

**Key Learning**: Phoenix state API doesn't accept applianceId field.

---

### Iteration 4: Phoenix State API - GET Requests
**Status**: ❌ FAILED

**What we tried**:
- GET `/api/phoenix/state` (no parameters)
- GET `/api/phoenix/state?entityId=...` (query params)
- GET `/api/phoenix/devicestates?entityId=...`

**Results**:
- All returned HTML pages instead of JSON
- Method Not Allowed (405) for `/devicestates`

**Key Learning**: Phoenix endpoints require specific POST payloads, don't support GET for device state.

---

### Iteration 5: Alternative API Endpoints
**Status**: ⚠️ PARTIAL

**What we tried**:
- `/api/activities` - 404
- `/api/cards` - 404  
- `/api/notifications` - 200 (no AQM data)
- `/api/behaviors/v2/automations` - 200 (found AQM automation/routine config but no current values)
- `/api/device-preferences` - 200 (no AQM data)
- `/api/phoenix` - 299 (deprecated)
- `/api/phoenix/smarthome/summary` - HTML response
- `/api/entities/{entityId}` - HTML response

**Results**:
- Found automation referencing instance #9 (IAQ) with trigger value of 85
- No endpoint returned current sensor readings

**Key Learning**: Automations API has references but not live data. Standard endpoints don't expose AQM state.

---

### Iteration 6: GraphQL Schema Introspection
**Status**: ✅ SUCCESS (schema info)

**What we tried**:
- Introspection query on `Endpoint` type
- Introspection query on `ApplicationFacingInterface` type

**Results**:
- Found 19 fields on Endpoint type
- Notable fields: `endpointReports`, `operations`, `interfaces`, `features`
- ApplicationFacingInterface only has: `instance`, `name`

**Key Learning**: GraphQL schema has potential state-related fields but queries using them failed validation.

---

### Iteration 7: GraphQL Extended Queries
**Status**: ❌ FAILED

**What we tried**:
- Query with `endpointReports`, `operations`, `interfaces.properties`, `features.properties`

**Results**:
- Multiple validation errors
- Fields don't exist as expected or require different syntax
- `properties` field doesn't exist on `ApplicationFacingInterface`

**Key Learning**: Schema introspection shows fields that aren't actually queryable or require specific subfield selection.

---

## Current Understanding

### What Works
1. ✅ Cookie-based authentication (18 cookies captured)
2. ✅ GraphQL device discovery at `/nexus/v1/graphql`
3. ✅ Retrieving device metadata (entity ID, appliance ID, capabilities)
4. ✅ Capability instance mapping (know which instance = which sensor)

### What Doesn't Work
1. ❌ Phoenix state API with entity ID
2. ❌ Phoenix state API with appliance ID  
3. ❌ GET requests to Phoenix endpoints
4. ❌ GraphQL queries for state/properties
5. ❌ Standard smart home endpoints

### Key Hypothesis
The Amazon Air Quality Monitor may use a **different architecture** than standard Alexa smart home devices:
- Might be a "cloud service" device (note the `AAA_SonarCloudService_` prefix in appliance ID)
- May require a specific API endpoint for "Sonar" cloud service devices
- Could use WebSocket/EventStream for real-time data
- Might only be accessible through Amazon's mobile app with different API
- AQM probably sends data to Alexa cloud, not directly queryable via Phoenix API; the app then fetches from there
- Investigate what AQM is sending over the local network (mDNS, UPnP, etc.)

---

## Next Iterations to Try

### Priority 1: Sonar Cloud Service API
- [ ] Search for `/api/sonar` endpoints
- [ ] Try `/api/cloud-service` or similar
- [ ] Look for AQM-specific endpoints

### Priority 2: Real-time Data Streams
- [ ] Check for WebSocket endpoints
- [ ] Look for Server-Sent Events (SSE) streams
- [ ] Test `/api/np/streaming` or similar

### Priority 3: Alternative GraphQL Queries
- [ ] Try mutation queries instead of query
- [ ] Look for `reportState` or `getState` mutations
- [ ] Test skill-specific GraphQL endpoints

### Priority 4: Reverse Engineering
- [ ] Monitor Alexa mobile app network traffic
- [ ] Inspect actual API calls when viewing AQM in app
- [ ] Check if there's a different base URL for AQM

### Priority 5: Home Assistant Deep Dive
- [ ] Study Home Assistant's Alexa Media Player source in detail
- [ ] Check if they handle AQM differently
- [ ] Look for AQM-specific code paths

---

### Iteration 8: Sonar Cloud Service Endpoints
**Status**: ❌ FAILED

**What we tried**:
- `/api/sonar/devices`, `/api/sonar/state`, `/api/sonar/device/{id}`
- `/api/cloudservice/devices`, `/api/cloudservice/state`  
- `/api/airquality/devices`, `/api/air-quality/state`, `/api/air-quality/device/{id}/state`
- `/api/smarthome/devices/state`, `/api/smarthome/devices/{id}/state`
- `/api/v2/smarthome/devices`
- `/api/phoenix/appliances/{id}`, `/api/phoenix/entities/{id}/state`

**Results**:
- Most returned HTML (200 OK but HTML pages)
- `/api/smarthome/devices/*` returned 404
- No JSON endpoints found for Sonar/AQM specific paths

**Key Learning**: Sonar/AQM doesn't have dedicated REST endpoints. All attempted paths return generic HTML pages.

---

### Iteration 9: Home Assistant Source Code Analysis
**Status**: ⚠️  CRITICAL FINDING

**What we tried**:
- Attempted to fetch Home Assistant Alexa Media Player source from GitHub
- Files returned 404 (repo structure may have changed)
- Performed web search for AQM integration patterns

**Results**:
- ⚠️ **MAJOR DISCOVERY**: Found GitHub issue #2867 in alexa_media_player repo
- Issue titled: "Air Quality Monitor No Longer Connecting Since Upgrading to HA 2025.03.1"
- **This means the AQM WAS working with Alexa Media Player before!**
- It broke in version 2025.3.1 (HA) / 5.6.0 (alexa_media)
- Users report: "entity reports as being missing, but it is in the Alexa app"
- 12+ users confirmed experiencing this issue

**Key Learning**: 
1. The Amazon AQM CAN be integrated and WAS working in earlier versions
2. Something changed in recent HA/alexa_media updates that broke it
3. The data IS accessible in the Alexa app, so the API exists
4. We need to look at OLDER versions of alexa_media_player to see how it worked

---

## Notes
- All research scripts archived in `tests/research/`
- Full API responses saved as JSON for reference
- Cookie authentication confirmed working across all requests
- Domain is UK-specific: `alexa.amazon.co.uk`

---

### Iteration 10: Echo Device Connection Theory
**Status**: ⚠️  PARTIAL - New Theory

**What we tried**:
- Retrieved list of registered devices via `/api/devices-v2/device`
- Tested bluetooth and connected device endpoints
- Examined AQM's `alexaDeviceIdentifierList` from GraphQL

**Results**:
- Found 2 devices in account (TV, "This Device") - no Echo speakers
- `/api/bluetooth` returns JSON but no AQM data
- AQM has own serial: `GAJ23005314600H3`, device type: `AEZME1X38KDRA`
- AQM is NOT a bluetooth peripheral, it's a WiFi device

**Key Learning**:
1. Reddit user confirmed AQM works with "devices connected to echo box" option checked
2. But AQM is WiFi-connected, not a peripheral
3. The "connected to echo" setting might affect which devices are polled/reported
4. AQM shows in GraphQL but not in Phoenix state API - different device category

---

## CRITICAL INSIGHT
The Amazon AQM integration EXISTS and worked before! Need to:
1. Check older versions of alexa_media_player (< 5.6.0)  
2. Find what changed between versions
3. Identify the working API pattern from older code

## Current Status - End of Session

### What We Know FOR SURE:
1. ✅ Cookie authentication works
2. ✅ GraphQL device discovery finds the AQM
3. ✅ We have all device metadata (entity ID, appliance ID, capabilities)
4. ✅ AQM **DID** work with Home Assistant Alexa Media Player before v5.6.0
5. ✅ Reddit users confirm it works with proper config

### What Doesn't Work:
1. ❌ Phoenix state API with entity ID → "TargetApplianceNotFoundException"
2. ❌ Phoenix state API with appliance ID → 400 Bad Request
3. ❌ All Sonar/AQM specific endpoints → HTML responses
4. ❌ GraphQL state queries → Validation errors
5. ❌ Standard smart home endpoints → 404 or HTML

### The Mystery:
- AQM appears in GraphQL as a smart home device with full capabilities
- Phoenix state API doesn't recognize it (different device category?)
- Home Assistant users say it works, but broke in recent version
- No clear API endpoint found that returns sensor values

### Next Steps (Priority Order):
1. **Check alexa_media_player commit history** around v5.6.0 to see what broke
2. **Review older versions** (v5.5.x, v5.4.x) source code for working implementation
3. **Monitor Alexa mobile app** network traffic when viewing AQM
4. **Try different GraphQL queries** - maybe mutations or different query structure
5. **Check if data comes via WebSocket/SSE** push instead of REST poll

---

## Notes
- All research scripts archived in `tests/research/`
- Full API responses saved as JSON for reference
- Cookie authentication confirmed working across all requests
- Domain is UK-specific: `alexa.amazon.co.uk`

---

### Iteration 13: Download alexapy Source from GitLab
**Status**: ✅ SUCCESS

**What we tried**:
- Discovered alexapy is hosted on GitLab, not GitHub: `https://gitlab.com/keatontaylor/alexapy`
- Downloaded current source from master branch

**Results**:
- Found alexapy project on GitLab
- Downloaded __init__.py, alexaapi.py, helpers.py, alexahttp2.py
- No RangeController or air quality references in current master branch

**Key Learning**: alexapy repository is on GitLab. Need to find specific version from when AQM was working.

---

### Iteration 14: Find Working alexapy Version
**Status**: ✅ SUCCESS

**What we tried**:
- Downloaded manifest.json from alexa_media_player v5.0.5
- Identified exact alexapy version: 1.29.5
- Downloaded alexapy 1.29.5 source files
- Downloaded sensor.py from alexa_media_player v5.0.5

**Results**:
- **CRITICAL DISCOVERY**: Found `parse_air_quality_from_coordinator` function in sensor.py
- Function is imported from `alexa_entity.py`  
- alexapy version used in working v5.0.5: **1.29.5**

**Key Learning**: AQM parsing logic exists in alexa_media_player, not alexapy. Need to examine alexa_entity.py.

---

### Iteration 15: Download alexa_entity.py
**Status**: ✅ SUCCESS

**What we tried**:
- Downloaded alexa_entity.py from v5.0.5
- Found `parse_air_quality_from_coordinator` function
- Traced data flow through `parse_value_from_coordinator`

**Results**:
- **BREAKTHROUGH**: Found the chain of functions:
  1. `get_entity_data()` - calls API
  2. `AlexaAPI.get_entity_state()` - makes HTTP request
  3. Returns coordinator data with capabilityStates
  4. `parse_air_quality_from_coordinator()` - extracts RangeController values

**Key Learning**: Data comes from `get_entity_state()` in alexapy. Need to examine that function.

---

### Iteration 16: CORRECT Endpoint Discovery
**Status**: 🎉 **BREAKTHROUGH SUCCESS**

**What we tried**:
- Found `get_entity_state()` in alexapy v1.29.5 alexaapi.py
- Endpoint: POST `/api/phoenix/state`
- Payload: `{"stateRequests": [{"entityId": "...", "entityType": "ENTITY"}]}`
- **KEY DIFFERENCE**: entityType = "ENTITY" (not "APPLIANCE"!)

**Results**:
```
HTTP 200 OK
Content-Type: application/json
Content-Encoding: gzip

Response: {
  "deviceStates": [{
    "entity": {"entityId": "95f34cda-2af4-443b-9b76-40544ea70cba"},
    "capabilityStates": [
      // 9 capability states as JSON strings
    ]
  }]
}

SENSOR VALUES RETRIEVED:
- Instance 4 (Humidity): 54.0
- Instance 5 (VOC): 2.0
- Instance 6 (PM2.5): 1.0
- Instance 7: 1.0
- Instance 8 (CO): 1.0
- Instance 9 (IAQ): 96.0
- Plus: TemperatureSensor: 20.75°C
- Plus: ToggleController (instance 11): ON
- Plus: EndpointHealth.connectivity: OK
```

**Key Learning**: 
✅ SOLUTION FOUND! The working endpoint structure is:
- POST (not GET)
- entityType: "ENTITY" (not "APPLIANCE")  
- Returns capabilityStates as JSON strings that need to be parsed
- RangeController values map to instances (4=Humidity, 5=VOC, 6=PM2.5, 8=CO, 9=IAQ)

**Next Steps**:
1. Update `amazon_collector.py` with correct endpoint and payload
2. Implement `capabilityStates` JSON parsing
3. Map instance IDs to sensor names
4. Test full integration

---

## Summary

**Total Iterations**: 16
**Status**: ✅ RESOLVED

**The Solution**:
```python
# CORRECT API call
POST https://alexa.amazon.co.uk/api/phoenix/state
Content-Type: application/json

{
  "stateRequests": [{
    "entityId": "95f34cda-2af4-443b-9b76-40544ea70cba",
    "entityType": "ENTITY"  # Critical: "ENTITY" not "APPLIANCE"
  }]
}

# Response structure
{
  "deviceStates": [{
    "entity": {"entityId": "..."},
    "capabilityStates": [
      '{"namespace":"Alexa.RangeController","name":"rangeValue","value":54.0,"instance":"4"}',
      // ... more JSON strings
    ]
  }]
}
```

**Key Insights**:
1. Source code analysis was the winning strategy - reverse-engineering the working v5.0.5
2. GitLab hosts alexapy, GitHub hosts alexa_media_player
3. The entityType distinction ("ENTITY" vs "APPLIANCE") was the critical difference
4. capabilityStates are JSON strings that need parsing
5. RangeController with instance IDs is the correct capability type for AQM sensors
