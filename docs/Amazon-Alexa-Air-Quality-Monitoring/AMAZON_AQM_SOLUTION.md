# Amazon Air Quality Monitor - Solution Found!

## Key Discovery

The Home Assistant **Alexa Media Player** integration successfully accesses the Amazon Smart Air Quality Monitor data. Here's what I learned from their source code:

### How It Works

1. **Endpoint**: The data comes from `/api/phoenix` (network details endpoint)
2. **Device Detection**: The Air Quality Monitor is identified by:
   - `friendlyDescription` == "Amazon Indoor Air Quality Monitor"
   - `applianceTypes` contains "AIR_QUALITY_MONITOR"
   - Has capabilities: `Alexa.TemperatureSensor` and `Alexa.RangeController`

3. **Data Structure**: The device exposes multiple sensors through capabilities:
   - Each capability has an `instance` ID
   - Each capability has an `assetId` starting with "Alexa.AirQuality"
   - Sensor types include: PM2.5, VOC, CO, Temperature, Humidity

### From Home Assistant Code

```python
def is_air_quality_sensor(appliance: dict[str, Any]) -> bool:
    """Is the given appliance the Air Quality Sensor."""
    return (
        appliance["friendlyDescription"] == "Amazon Indoor Air Quality Monitor"
        and "AIR_QUALITY_MONITOR" in appliance.get("applianceTypes", [])
        and has_capability(appliance, "Alexa.TemperatureSensor", "temperature")
        and has_capability(appliance, "Alexa.RangeController", "rangeValue")
    )
```

The integration then parses the capabilities to extract individual sensors:

```python
for cap in appliance["capabilities"]:
    instance = cap.get("instance")
    if not instance:
        continue

    friendlyName = cap["resources"].get("friendlyNames")
    for entry in friendlyName:
        assetId = entry["value"].get("assetId")
        if not assetId or not assetId.startswith("Alexa.AirQuality"):
            continue

        unit = cap["configuration"]["unitOfMeasure"]
        sensor = {
            "sensorType": assetId,
            "instance": instance,
            "unit": unit,
        }
```

## Current Challenge

When I try to access `/api/phoenix`, I get:
- Status 299 (unusual status code)
- Empty response

This suggests either:
1. **Missing Headers/Parameters**: The request needs specific headers or query parameters
2. **Different Domain**: Might need to use a different Amazon domain (e.g., `.co.uk` vs `.com`)
3. **Cookie Issues**: The cookies might not be valid for this specific endpoint
4. **Library Dependency**: The `alexapy` library might handle authentication differently

## Recommended Solutions

### Option 1: Use alexapy Library (RECOMMENDED)
Instead of reimplementing the wheel, we should use the `alexapy` Python library that Home Assistant uses:

```bash
pip install alexapy
```

This library handles:
- Proper authentication
- Correct API endpoints
- Response parsing
- Cookie management

### Option 2: Inspect Actual Traffic
Use a proxy to see exactly what Home Assistant sends:
1. Set up mitmproxy or Charles Proxy
2. Configure Home Assistant to use the proxy
3. Capture the actual `/api/phoenix` request
4. See exact headers, cookies, and parameters

### Option 3: Manual Browser Inspection
1. Log into alexa.amazon.com in browser
2. Open Developer Tools → Network tab
3. Navigate to Devices → Air Quality Monitor
4. Find the API call that loads the data
5. Copy the exact request format

## Next Steps

I recommend **Option 1** - using the `alexapy` library. This is the battle-tested solution that Home Assistant uses. Would you like me to:

1. Install `alexapy` and update our collector to use it?
2. Or help you set up traffic inspection to see the exact API calls?

The infrastructure is all in place - we just need to use the right library to make the API calls!

## Files Created
- `test_phoenix_endpoint.py` - Test script for phoenix endpoint
- `test_phoenix_variations.py` - Tests different endpoint variations
- This documentation file

## Reference
- Home Assistant Alexa Media Player: https://github.com/alandtse/alexa_media_player
- Key file: `custom_components/alexa_media/alexa_entity.py`
- Function: `is_air_quality_sensor()` and `parse_alexa_entities()`
