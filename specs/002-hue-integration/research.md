# Research: Philips Hue Temperature Collection

**Feature**: 002-hue-integration  
**Date**: 2025-11-18  
**Status**: Complete

## Overview

This document resolves technical unknowns identified in the Technical Context section of plan.md, specifically around Hue API client library selection and best practices for interacting with the Philips Hue Bridge API.

---

## Research Task 1: Hue API Client Library Selection

### Decision
Use **`phue`** library (unofficial Python wrapper for Philips Hue API)

### Rationale
1. **Simplicity**: `phue` provides a straightforward Python interface matching our "quick and dirty" principle
2. **Local API Support**: Works with local Bridge API (no cloud dependency), aligning with security requirements
3. **Active Development**: Well-maintained with 1.1k+ GitHub stars, last updated 2023
4. **Authentication Built-in**: Handles button press authentication flow out of the box
5. **Sensor Support**: Full support for sensor queries including temperature readings
6. **Minimal Dependencies**: Lightweight with only `requests` as dependency
7. **MIT License**: Permissive licensing suitable for this project

### Alternatives Considered

#### Option A: Official Hue API (direct HTTP requests)
- **Pros**: No external dependencies, full control, official documentation
- **Cons**: Requires manual implementation of authentication flow, discovery, error handling - contradicts "quick and dirty" principle
- **Rejected Because**: Too much boilerplate for a simple data collection task

#### Option B: `aiohue` (async Python client)
- **Pros**: Async support, modern Python patterns, active development
- **Cons**: Adds async complexity, overkill for simple 5-minute polling intervals, steeper learning curve
- **Rejected Because**: Async not needed for this use case; simpler synchronous approach preferred

#### Option C: `hue-python-rgb-hack`
- **Pros**: Simple, focuses on color control
- **Cons**: Primarily for light control, limited sensor support, less maintained
- **Rejected Because**: Not optimized for sensor data collection

### Implementation Notes
```python
# Installation
pip install phue

# Basic usage pattern
from phue import Bridge

# Authentication (one-time button press)
bridge = Bridge('192.168.1.X')  # First run prompts for button press
bridge.connect()

# Get sensors
sensors = bridge.get_sensor_objects('ZLLTemperature')  # Filter by temperature type

# Read temperature
for sensor in sensors:
    temp_celsius = sensor.state['temperature'] / 100.0  # Convert from 0.01°C units
    print(f"{sensor.name}: {temp_celsius}°C")
```

---

## Research Task 2: Hue Bridge Discovery Best Practices

### Decision
Use **mDNS discovery with fallback to manual IP configuration**

### Rationale
1. **User Experience**: Automatic discovery provides better first-run experience
2. **Resilience**: Manual fallback handles networks where mDNS is blocked or unreliable
3. **DHCP Protection**: Discovery handles IP address changes gracefully
4. **Standard Protocol**: Hue Bridge advertises via `_hue._tcp.local` mDNS service

### Implementation Approach
```python
# Option 1: Use phue's built-in discovery
from phue import Bridge, discover_nupnp

bridges = discover_nupnp()  # Returns list of bridge IPs on network

# Option 2: Manual configuration fallback
# In config.yaml:
# hue:
#   bridge_ip: "192.168.1.100"  # Optional: skip discovery if set
#   auto_discover: true          # Default: true
```

### Best Practices
- Store discovered IP in config file after first successful connection
- Re-run discovery only if stored IP fails to connect
- Log discovery attempts for troubleshooting
- Timeout discovery after 10 seconds to avoid hanging

---

## Research Task 3: Hue API Rate Limits & Polling Strategy

### Decision
**10 requests per second limit, 1 request per collection cycle sufficient**

### Rationale
1. **Official Limit**: Hue Bridge enforces ~10 requests/second limit (local API)
2. **Our Use Case**: Single batch request per 5-minute cycle = 0.003 req/sec (well within limits)
3. **Batch Efficiency**: Single `/sensors` endpoint returns all sensors, avoiding multiple requests
4. **No Throttling Needed**: 5-minute intervals naturally respect rate limits

### Implementation Strategy
```python
# Efficient: Single request for all sensors
all_sensors = bridge.get_api()['sensors']
temp_sensors = {k: v for k, v in all_sensors.items() 
                if v['type'] == 'ZLLTemperature'}

# Inefficient (avoid): Individual requests per sensor
# for sensor_id in sensor_ids:
#     sensor_data = bridge.get_sensor(sensor_id)  # Multiple API calls
```

### Error Handling
- Implement exponential backoff (1s, 2s, 4s) for failed requests as per constitution
- Log rate limit errors if encountered (unlikely with our frequency)
- Continue with partial data if some sensors fail to respond

---

## Research Task 4: Temperature Data Validation & Anomaly Detection

### Decision
**Client-side validation with configurable bounds and anomaly flagging**

### Rationale
1. **Data Quality**: Catch sensor malfunctions early (e.g., reporting 100°C)
2. **Constitution Compliance**: 0°C to 40°C indoor range specified in constitution
3. **Analysis Readiness**: Flagged anomalies can be filtered or investigated during analysis
4. **Non-Blocking**: Store anomalous readings with flag rather than rejecting (preserves sensor history)

### Validation Rules
```python
INDOOR_TEMP_MIN = 0.0   # °C
INDOOR_TEMP_MAX = 40.0  # °C

def validate_temperature(temp_celsius, device_id):
    """
    Validate temperature reading and flag anomalies.
    
    Returns: (is_valid, is_anomalous)
    - is_valid: False only if data is malformed/missing
    - is_anomalous: True if outside expected range but still stored
    """
    if temp_celsius is None:
        return (False, False)
    
    if temp_celsius < INDOOR_TEMP_MIN or temp_celsius > INDOOR_TEMP_MAX:
        logger.warning(f"Anomalous temperature from {device_id}: {temp_celsius}°C")
        return (True, True)  # Valid but anomalous
    
    return (True, False)
```

### Database Schema Extension
```sql
-- Add anomaly flag to readings table
ALTER TABLE temperature_readings 
ADD COLUMN is_anomalous BOOLEAN DEFAULT 0;
```

---

## Research Task 5: Hue Sensor Metadata & Location Mapping

### Decision
**Use Hue app room assignments, fallback to sensor name, store mappings in config**

### Rationale
1. **User-Friendly**: Leverages existing room names from Hue app
2. **Consistency**: Matches how users mentally organize their sensors
3. **Flexibility**: Config file allows overriding Hue names if needed
4. **Documentation**: Location mappings are explicit and auditable

### Data Available from Hue API
```json
{
  "1": {
    "name": "Hue temperature sensor 1",
    "type": "ZLLTemperature",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "uniqueid": "00:17:88:01:02:03:04:05-02-0402",
    "state": {
      "temperature": 2134,  // 21.34°C
      "lastupdated": "2025-11-18T10:30:00"
    },
    "config": {
      "on": true,
      "battery": 100,
      "reachable": true
    }
  }
}
```

### Location Mapping Strategy
```yaml
# config.yaml
hue:
  sensor_locations:
    "00:17:88:01:02:03:04:05-02-0402": "Living Room"
    "00:17:88:01:02:03:04:06-02-0402": "Bedroom"
  fallback_to_name: true  # Use sensor.name if not in mappings
```

### Implementation
```python
def get_sensor_location(sensor, config):
    """Determine sensor location from config or Hue metadata."""
    unique_id = sensor['uniqueid']
    
    # Priority 1: Explicit config mapping
    if unique_id in config['hue']['sensor_locations']:
        return config['hue']['sensor_locations'][unique_id]
    
    # Priority 2: Hue sensor name
    if config['hue'].get('fallback_to_name', True):
        return sensor['name']
    
    # Priority 3: Unknown
    return f"Unknown ({unique_id[:8]})"
```

---

## Research Task 6: SQLite Schema Design for Time-Series Data

### Decision
**Single table with indexed timestamp + device_id, optional metadata columns**

### Rationale
1. **Simplicity**: Single table matches "quick and dirty" principle
2. **Query Performance**: Composite index on (device_id, timestamp) enables efficient time-range queries
3. **Flexibility**: Optional columns accommodate varying metadata availability
4. **Analysis-Ready**: Schema supports common queries (device trends, time ranges, anomaly filtering)

### Schema Design
```sql
CREATE TABLE IF NOT EXISTS temperature_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,              -- ISO 8601 with timezone
    device_id TEXT NOT NULL,              -- Format: hue:sensor_unique_id
    temperature_celsius REAL NOT NULL,    -- Standard Celsius
    location TEXT NOT NULL,               -- Room/zone name
    device_type TEXT NOT NULL,            -- 'hue_sensor'
    is_anomalous BOOLEAN DEFAULT 0,       -- Validation flag
    battery_level INTEGER,                -- Optional: 0-100
    signal_strength INTEGER,              -- Optional: reachable boolean → 0/1
    raw_api_response TEXT,                -- Optional: JSON for debugging
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(device_id, timestamp)          -- Prevent duplicates
);

-- Performance index for common queries
CREATE INDEX IF NOT EXISTS idx_device_timestamp 
ON temperature_readings(device_id, timestamp);

-- Index for time-range queries across all devices
CREATE INDEX IF NOT EXISTS idx_timestamp 
ON temperature_readings(timestamp);

-- Index for anomaly analysis
CREATE INDEX IF NOT EXISTS idx_anomalous 
ON temperature_readings(is_anomalous) 
WHERE is_anomalous = 1;
```

### Query Performance Considerations
- Typical query: Last week for device → uses idx_device_timestamp
- Typical query: All devices at time range → uses idx_timestamp
- Anomaly investigation → uses idx_anomalous (partial index)
- Expected dataset: ~5 sensors × 288 readings/day × 365 days = ~525k rows/year (lightweight for SQLite)

---

## Research Task 7: Error Handling & Retry Strategy

### Decision
**3 retries with exponential backoff (1s, 2s, 4s), log and continue on failure**

### Rationale
1. **Constitution Compliance**: Specified retry policy (3 attempts, exponential backoff)
2. **Network Resilience**: Handles transient network issues without data loss
3. **Non-Blocking**: Failed sensors don't stop collection from other sensors
4. **Observability**: Logging enables post-mortem analysis of failures

### Implementation Pattern
```python
import time
import logging

def collect_with_retry(bridge, max_retries=3):
    """Collect sensor data with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            sensors = bridge.get_api()['sensors']
            return sensors
        except Exception as e:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            logging.warning(f"Collection attempt {attempt+1} failed: {e}")
            
            if attempt < max_retries - 1:
                logging.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logging.error(f"Collection failed after {max_retries} attempts")
                return None  # Graceful failure
    
    return None
```

### Failure Scenarios
| Scenario | Behavior |
|----------|----------|
| Bridge offline | Retry 3x, log error, skip cycle |
| Single sensor offline | Continue collecting from other sensors |
| Network timeout | Exponential backoff, retry up to 3x |
| Authentication expired | Log critical error, require manual re-auth |
| Rate limit (unlikely) | Exponential backoff handles it |

---

## Research Task 8: Secrets Management Best Practices

### Decision
**YAML-based secrets file with gitignore, template for onboarding**

### Rationale
1. **Constitution Compliance**: Secrets in gitignored file, no hardcoded credentials
2. **Developer Experience**: YAML is human-readable and easy to edit
3. **Onboarding**: Template file (`secrets.yaml.example`) documents required secrets
4. **Security**: Secrets never committed to version control

### File Structure
```yaml
# secrets.yaml (gitignored)
hue:
  api_key: "abc123def456ghi789"  # Generated during button press auth
  bridge_id: "001788fffe100200"  # Bridge unique identifier

# secrets.yaml.example (committed)
hue:
  api_key: "YOUR_HUE_API_KEY_HERE"  # Generated during setup - see docs
  bridge_id: "YOUR_BRIDGE_ID_HERE"  # Found during discovery - see docs
```

### Validation
```python
# In config/validator.py
def validate_hue_secrets(secrets):
    """Validate Hue secrets are present and formatted correctly."""
    required = ['api_key', 'bridge_id']
    
    if 'hue' not in secrets:
        raise ValueError("Missing 'hue' section in secrets.yaml")
    
    for field in required:
        if field not in secrets['hue']:
            raise ValueError(f"Missing required Hue secret: {field}")
        
        if secrets['hue'][field].startswith('YOUR_'):
            raise ValueError(f"Hue secret '{field}' not configured (still has placeholder)")
    
    return True
```

---

## Summary of Resolved Unknowns

| Original Unknown | Resolution |
|-----------------|------------|
| Primary Dependencies | `phue` library (simple, local API, MIT license) |
| Hue Bridge Discovery | mDNS with manual IP fallback |
| API Rate Limits | 10 req/s limit, 1 req/cycle sufficient (no throttling needed) |
| Temperature Validation | 0-40°C bounds, flag anomalies but store them |
| Location Mapping | Use Hue room assignments, config overrides available |
| Database Schema | Single table, composite indexes, optional metadata columns |
| Retry Strategy | 3 attempts, exponential backoff (1s, 2s, 4s) |
| Secrets Management | YAML file (gitignored) with committed template |

---

## Dependencies Added

```txt
# requirements.txt additions
phue==1.1          # Philips Hue API client
```

---

## Next Steps

Phase 0 research complete. Ready to proceed to Phase 1:
- Generate data-model.md (entity definitions)
- Generate contracts/ (API samples, database schema, config templates)
- Generate quickstart.md (setup and usage instructions)
- Update agent context with new dependencies
