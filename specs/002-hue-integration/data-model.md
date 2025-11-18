# Data Model: Philips Hue Temperature Collection

**Feature**: 002-hue-integration  
**Date**: 2025-11-18  
**Status**: Complete

## Overview

This document defines the core entities, their relationships, and state transitions for the Philips Hue temperature collection feature. Entities map directly to the database schema and API contracts.

---

## Entity: Temperature Reading

**Purpose**: Represents a single temperature measurement from a Hue sensor at a specific point in time.

### Fields

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `id` | Integer | Auto | Auto-increment | Primary key (database only) |
| `timestamp` | String (ISO 8601) | Yes | ISO 8601 format with timezone | When the reading was taken |
| `device_id` | String | Yes | Format: `hue:<sensor_unique_id>` | Composite device identifier |
| `temperature_celsius` | Float | Yes | Must be numeric | Temperature in Celsius (converted from 0.01°C units) |
| `location` | String | Yes | Non-empty string | Room or zone name (from Hue metadata or config) |
| `device_type` | String | Yes | Fixed: `hue_sensor` | Type identifier for multi-source system |
| `is_anomalous` | Boolean | No | Default: `false` | Flag for readings outside 0-40°C range |
| `battery_level` | Integer | No | Range: 0-100 or null | Battery percentage (if available from sensor) |
| `signal_strength` | Integer | No | 0 (unreachable) or 1 (reachable) | Connectivity status |
| `raw_api_response` | String (JSON) | No | Valid JSON or null | Full API response for debugging |
| `created_at` | String (ISO 8601) | Auto | Auto-generated | Database insertion timestamp |

### Validation Rules

```python
def validate_reading(reading):
    """Validate temperature reading before storage."""
    errors = []
    
    # Required fields
    if not reading.get('timestamp'):
        errors.append("Missing required field: timestamp")
    if not reading.get('device_id'):
        errors.append("Missing required field: device_id")
    if reading.get('temperature_celsius') is None:
        errors.append("Missing required field: temperature_celsius")
    if not reading.get('location'):
        errors.append("Missing required field: location")
    if not reading.get('device_type'):
        errors.append("Missing required field: device_type")
    
    # Format validation
    if reading.get('device_id') and not reading['device_id'].startswith('hue:'):
        errors.append("device_id must start with 'hue:'")
    
    if reading.get('device_type') != 'hue_sensor':
        errors.append("device_type must be 'hue_sensor' for this feature")
    
    # Range validation (anomaly detection)
    temp = reading.get('temperature_celsius')
    if temp is not None:
        if temp < 0.0 or temp > 40.0:
            reading['is_anomalous'] = True  # Flag but don't reject
    
    # Optional field validation
    battery = reading.get('battery_level')
    if battery is not None and (battery < 0 or battery > 100):
        errors.append("battery_level must be between 0 and 100")
    
    return errors
```

### Relationships

- **One-to-One** with Hue Sensor (via `device_id`)
- **Many** Temperature Readings per Hue Sensor over time
- No foreign key constraints (supports sensor addition/removal without schema changes)

### Uniqueness Constraint

- **Composite Unique Key**: (`device_id`, `timestamp`)
- **Rationale**: Prevents duplicate readings for the same sensor at the same time
- **Behavior**: Database insert fails on duplicate, application logs and skips

---

## Entity: Hue Sensor

**Purpose**: Represents a physical Philips Hue motion sensor with temperature capability.

**Note**: This entity is not stored in the database persistently, but is discovered and cached at runtime.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sensor_id` | String | Yes | Hue Bridge internal sensor ID (e.g., "1", "2") |
| `unique_id` | String | Yes | Globally unique sensor identifier (MAC-based) |
| `name` | String | Yes | User-assigned sensor name from Hue app |
| `model_id` | String | Yes | Sensor model identifier (e.g., "SML001") |
| `manufacturer` | String | Yes | Always "Philips" for Hue sensors |
| `sensor_type` | String | Yes | Always "ZLLTemperature" for temperature sensors |
| `location_name` | String | Yes | Mapped room/zone (from config or Hue name) |
| `is_reachable` | Boolean | Yes | Whether sensor is currently online |
| `battery_level` | Integer | No | Battery percentage (0-100) |
| `last_updated` | String (ISO 8601) | No | Last API update timestamp from Bridge |

### State Diagram

```
┌─────────────┐
│  Discovered │ ← Initial state when sensor found on Bridge
└──────┬──────┘
       │
       ├───→ [Online] ──→ [Collecting Data]
       │                        │
       │                        ├──→ Battery OK (>20%)
       │                        └──→ Battery Low (≤20%) [Warning logged]
       │
       └───→ [Offline/Unreachable] ──→ [Skipped in Collection Cycle]
                                           │
                                           └──→ [Online] (when reachable again)
```

### Discovery Process

```python
def discover_hue_sensors(bridge, config):
    """
    Discover temperature-capable sensors from Hue Bridge.
    
    Returns: List of HueSensor objects
    """
    sensors = []
    api_sensors = bridge.get_api()['sensors']
    
    for sensor_id, sensor_data in api_sensors.items():
        # Filter for temperature sensors only
        if sensor_data['type'] != 'ZLLTemperature':
            continue
        
        sensor = {
            'sensor_id': sensor_id,
            'unique_id': sensor_data['uniqueid'],
            'name': sensor_data['name'],
            'model_id': sensor_data['modelid'],
            'manufacturer': sensor_data['manufacturername'],
            'sensor_type': sensor_data['type'],
            'location_name': get_sensor_location(sensor_data, config),
            'is_reachable': sensor_data['config']['reachable'],
            'battery_level': sensor_data['config'].get('battery'),
            'last_updated': sensor_data['state'].get('lastupdated')
        }
        
        sensors.append(sensor)
    
    return sensors
```

---

## Entity: Bridge Connection

**Purpose**: Represents the authenticated connection to a Philips Hue Bridge.

**Note**: Configuration entity, stored in `secrets.yaml`, not in database.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bridge_ip` | String | Yes* | IPv4 address of Bridge (e.g., "192.168.1.100") |
| `api_key` | String | Yes | Authentication token (generated via button press) |
| `bridge_id` | String | Yes | Unique Bridge identifier (MAC-based) |
| `auto_discover` | Boolean | No | Enable/disable mDNS discovery (default: true) |

\* Required in config if `auto_discover` is false; otherwise optional (discovered dynamically)

### State Transitions

```
┌─────────────────┐
│  Unauthenticated│
└────────┬────────┘
         │
         ├─→ [Discovery] ──→ Bridge IP found
         │                      │
         │                      ├─→ [Button Press] ──→ API key generated
         │                      │                          │
         │                      │                          └─→ [Authenticated]
         │                      │                                    │
         │                      │                                    ├─→ [Connected] ← Active
         │                      │                                    │        │
         │                      │                                    │        └─→ Collection cycles
         │                      │                                    │
         │                      │                                    └─→ [Connection Failed] ← Retry
         │                      │
         │                      └─→ [Button Not Pressed] ──→ Error
         │
         └─→ [Manual IP] ──→ [Button Press] (same flow as above)
```

### Authentication Flow

```python
def authenticate_bridge(config_ip=None):
    """
    Authenticate with Hue Bridge.
    
    Args:
        config_ip: Optional manual IP from config
    
    Returns:
        (bridge_ip, api_key, bridge_id)
    """
    # Step 1: Discover or use manual IP
    if config_ip:
        bridge_ip = config_ip
    else:
        bridges = discover_nupnp()
        if not bridges:
            raise Exception("No Hue Bridge found. Set bridge_ip in config.")
        bridge_ip = bridges[0]['internalipaddress']
    
    # Step 2: Attempt connection
    try:
        bridge = Bridge(bridge_ip)
        bridge.connect()  # Prompts for button press on first run
        
        # Step 3: Store credentials
        api_key = bridge.username  # Generated API key
        bridge_id = bridge.config['bridgeid']
        
        return (bridge_ip, api_key, bridge_id)
    
    except PhueRegistrationException:
        raise Exception("Press button on Hue Bridge and try again")
```

---

## Data Flow Diagram

```
┌──────────────────┐
│  Hue Bridge API  │
│   (Local HTTP)   │
└────────┬─────────┘
         │
         │ GET /api/<key>/sensors
         │
         ▼
┌──────────────────────┐
│  Sensor Discovery    │ ← Filter by type: ZLLTemperature
│  (Runtime Cache)     │
└────────┬─────────────┘
         │
         │ For each sensor
         │
         ▼
┌──────────────────────┐
│  Temperature         │ ← Convert 0.01°C → Celsius
│  Reading (Staging)   │ ← Add timestamp, device_id
└────────┬─────────────┘
         │
         │ Validation
         │
         ▼
┌──────────────────────┐
│  Validate Reading    │ ← Check required fields
│                      │ ← Flag anomalies (0-40°C)
└────────┬─────────────┘
         │
         │ Valid
         │
         ▼
┌──────────────────────┐
│  SQLite Database     │
│  temperature_readings│ ← INSERT with UNIQUE constraint
└──────────────────────┘
```

---

## Entity Mapping to Database Schema

### `temperature_readings` Table

Maps directly to **Temperature Reading** entity:

```sql
CREATE TABLE IF NOT EXISTS temperature_readings (
    -- Temperature Reading entity fields
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    device_id TEXT NOT NULL,
    temperature_celsius REAL NOT NULL,
    location TEXT NOT NULL,
    device_type TEXT NOT NULL,
    is_anomalous BOOLEAN DEFAULT 0,
    battery_level INTEGER,
    signal_strength INTEGER,
    raw_api_response TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(device_id, timestamp)
);
```

### Runtime Entities (Not Persisted)

- **Hue Sensor**: Cached in-memory during collection cycle
- **Bridge Connection**: Stored in `config/secrets.yaml`

---

## Sample Data

### Temperature Reading (JSON)

```json
{
  "timestamp": "2025-11-18T14:30:00+00:00",
  "device_id": "hue:00:17:88:01:02:03:04:05-02-0402",
  "temperature_celsius": 21.34,
  "location": "Living Room",
  "device_type": "hue_sensor",
  "is_anomalous": false,
  "battery_level": 87,
  "signal_strength": 1,
  "raw_api_response": "{\"state\":{\"temperature\":2134,\"lastupdated\":\"2025-11-18T14:30:00\"},\"config\":{\"on\":true,\"battery\":87,\"reachable\":true}}"
}
```

### Hue Sensor (Runtime Object)

```python
{
    'sensor_id': '1',
    'unique_id': '00:17:88:01:02:03:04:05-02-0402',
    'name': 'Hue temperature sensor 1',
    'model_id': 'SML001',
    'manufacturer': 'Philips',
    'sensor_type': 'ZLLTemperature',
    'location_name': 'Living Room',
    'is_reachable': True,
    'battery_level': 87,
    'last_updated': '2025-11-18T14:30:00'
}
```

---

## Validation Summary

| Entity | Validation Type | Rules |
|--------|----------------|-------|
| **Temperature Reading** | Required Fields | timestamp, device_id, temperature_celsius, location, device_type |
| **Temperature Reading** | Format | device_id starts with `hue:`, device_type = `hue_sensor` |
| **Temperature Reading** | Range (Anomaly) | 0°C ≤ temp ≤ 40°C (flag if outside, don't reject) |
| **Temperature Reading** | Uniqueness | Composite: (device_id, timestamp) |
| **Hue Sensor** | Discovery Filter | sensor_type = `ZLLTemperature` |
| **Bridge Connection** | Authentication | API key generated via button press |

---

## Next Steps

Data model complete. Ready to generate:
- Contract files (API samples, database schema SQL, config templates)
- Quickstart documentation
