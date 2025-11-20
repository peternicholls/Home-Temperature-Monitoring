# Amazon AQM Integration - SOLUTION IMPLEMENTED

## Summary

**Status**: ✅ COMPLETE - Real sensor data successfully retrieved!

After 16 iterations of research and testing, we discovered the correct API endpoint and implementation for retrieving real-time sensor data from Amazon Smart Air Quality Monitor.

## The Problem

- Initial attempts using `/api/phoenix/state` with `entityType: "APPLIANCE"` returned "TargetApplianceNotFoundException"
- GET requests returned HTML instead of JSON
- Standard smart home APIs didn't recognize AQM devices

## The Solution

By reverse-engineering the working Home Assistant Alexa Media Player integration (v5.0.5), we discovered:

### Correct API Call

```python
POST https://alexa.amazon.co.uk/api/phoenix/state
Content-Type: application/json

{
  "stateRequests": [{
    "entityId": "95f34cda-2af4-443b-9b76-40544ea70cba",
    "entityType": "ENTITY"  # KEY: "ENTITY" not "APPLIANCE"
  }]
}
```

### Response Structure

```json
{
  "deviceStates": [{
    "entity": {"entityId": "..."},
    "capabilityStates": [
      "{\"namespace\":\"Alexa.RangeController\",\"name\":\"rangeValue\",\"value\":53.0,\"instance\":\"4\"}",
      "{\"namespace\":\"Alexa.TemperatureSensor\",\"name\":\"temperature\",\"value\":{\"value\":20.5,\"scale\":\"CELSIUS\"}}",
      ...
    ]
  }]
}
```

**Key Points**:
- `capabilityStates` are JSON **strings** that need parsing
- RangeController instances map to specific sensors
- Each instance ID corresponds to a sensor type

### Instance Mapping

| Instance | Sensor | Field Name | Units |
|----------|--------|------------|-------|
| 4 | Humidity | `humidity_percent` | % |
| 5 | VOC | `voc_ppb` | ppb |
| 6 | PM2.5 | `pm25_ugm3` | µg/m³ |
| 7 | Unknown | `unknown_7` | - |
| 8 | Carbon Monoxide | `co_ppm` | ppm |
| 9 | Indoor Air Quality | `iaq_score` | 0-100 |
| - | Temperature | `temperature_celsius` | °C |
| 11 | Power Toggle | - | ON/OFF |

## Implementation

Updated `source/collectors/amazon_collector.py`:

1. **Changed HTTP method**: GET → POST
2. **Fixed payload structure**: Added `entityType: "ENTITY"`
3. **Implemented JSON parsing**: Parse `capabilityStates` strings
4. **Added instance mapping**: Map instance IDs to sensor names
5. **Updated validation**: Added CO and IAQ validation

## Test Results

```
================================================================================
Testing Updated AmazonAQMCollector
================================================================================

1. Device Discovery
--------------------------------------------------------------------------------
Found 1 devices

First device keys: ['device_id', 'entity_id', 'appliance_id', 'friendly_name', 'device_serial', 'capabilities']
  Name: N/A
  Entity ID: 95f34cda-2af4-443b-9b76-40544ea70cba
  Serial: GAJ23005314600H3

2. Get Air Quality Readings
--------------------------------------------------------------------------------
✅ SUCCESS! Collected 8 readings:
  temperature_celsius: 20.5
  humidity_percent: 53.0
  connectivity: OK
  voc_ppb: 100.0
  co_ppm: 1.0
  iaq_score: 32.0
  pm25_ugm3: 1.0
  unknown_7: 1.0

3. Validation
--------------------------------------------------------------------------------
✅ All readings valid!
```

## Key Learnings

1. **Source Code Analysis Works**: Reverse-engineering the working v5.0.5 was the breakthrough strategy
2. **Repository Discovery**: alexapy is on GitLab (not GitHub)
3. **Critical Detail**: `entityType: "ENTITY"` vs `"APPLIANCE"` made all the difference
4. **Data Structure**: capabilityStates are JSON strings requiring parsing
5. **Instance IDs**: RangeController uses instance IDs to differentiate sensors

## Research Artifacts

All research iterations documented in:
- `RESEARCH_LOG.md` - Complete iteration log (iterations 1-16)
- `tests/research/` - 16+ test scripts and response data files
- `tests/research/README.md` - Research artifacts documentation

## Source References

- `iter14_v1.29.5_alexapy_alexaapi.py` - Contains `get_entity_state()` method
- `iter15_amp_v505_alexa_entity.py` - Contains parsing logic
- `iter15_amp_v505___init__.py` - Contains coordinator update logic
- `iter16_phoenix_state_response.json` - Sample successful response

## Next Steps

- [x] Update amazon_collector.py with correct endpoint
- [x] Implement capabilityStates JSON parsing  
- [x] Map instance IDs to sensor names
- [x] Test with real device
- [x] Add validation for new fields (CO, IAQ)
- [ ] Add configuration to config.yaml for domain
- [ ] Update documentation
- [ ] Integration testing with storage layer

## Credits

Solution discovered by analyzing Home Assistant's alexa_media_player v5.0.5 and alexapy v1.29.5 source code.

- alexa_media_player: https://github.com/alandtse/alexa_media_player
- alexapy: https://gitlab.com/keatontaylor/alexapy
