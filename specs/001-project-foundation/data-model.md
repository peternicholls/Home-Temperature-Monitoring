# Phase 1: Data Model - Sprint 0 Project Foundation

**Feature**: 001-project-foundation  
**Created**: 2025-11-18  
**Purpose**: Define data entities, relationships, and validation rules

## Entities

### 1. Configuration
**Purpose**: Application settings that control behavior but are not sensitive  
**Lifecycle**: Loaded at startup, immutable during runtime  
**Source**: `config/config.yaml`

#### Fields
| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| `collection_interval_seconds` | integer | Yes | 300 | >= 60 | How often to collect data (5 min = 300s) |
| `database_path` | string | Yes | `data/readings.db` | Valid path | SQLite database file location |
| `log_level` | string | Yes | `INFO` | DEBUG\|INFO\|WARNING\|ERROR | Logging verbosity |
| `retry_attempts` | integer | Yes | 3 | 1-10 | Number of retry attempts for API calls |
| `retry_backoff_base` | float | Yes | 1.0 | > 0 | Base seconds for exponential backoff |

#### Validation Rules
- Collection interval must allow completing all collectors before next cycle
- Database path directory must be writable
- Log level must be valid Python logging level
- Retry configuration must prevent infinite loops

---

### 2. Secrets
**Purpose**: Sensitive credentials for API authentication  
**Lifecycle**: Loaded at startup, never logged, immutable during runtime  
**Source**: `config/secrets.yaml` (gitignored)

#### Fields
| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| `hue_api_key` | string | No* | - | Non-empty if present | Philips Hue Bridge API key |
| `hue_bridge_ip` | string | No* | - | Valid IP address | Hue Bridge local IP |
| `nest_client_id` | string | No* | - | Non-empty if present | Google OAuth client ID |
| `nest_client_secret` | string | No* | - | Non-empty if present | Google OAuth client secret |
| `nest_refresh_token` | string | No* | - | Non-empty if present | Google OAuth refresh token |
| `weather_api_key` | string | No* | - | Non-empty if present | Weather API key |

*Required for respective collector sprints, optional for foundation sprint

#### Validation Rules
- No secrets logged or exposed in error messages
- Secrets file must have restrictive permissions (600)
- Empty/missing secrets acceptable if collector not enabled

---

### 3. TemperatureReading
**Purpose**: Single temperature measurement with metadata  
**Lifecycle**: Created by collectors, persisted to database, immutable after insertion  
**Storage**: `readings` table in SQLite database

#### Fields
| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| `id` | integer | Auto | Auto-increment | Unique, PK | Internal record ID |
| `timestamp` | datetime | Yes | - | ISO 8601 with TZ | When reading was taken |
| `device_id` | string | Yes | - | Composite format | `source_type:device_id` |
| `temperature_celsius` | float | Yes | - | -40 to 50 | Temperature reading |
| `location` | string | Yes | - | Non-empty | Room/zone or "outside" |
| `device_type` | string | Yes | - | Enum | hue_sensor\|nest_thermostat\|weather_api |
| `humidity_percent` | float | No | NULL | 0-100 | Relative humidity if available |
| `battery_level` | integer | No | NULL | 0-100 | Battery percentage if applicable |
| `signal_strength` | integer | No | NULL | 0-100 | Connectivity quality if available |
| `thermostat_mode` | string | No | NULL | Enum | heating\|cooling\|off\|away |
| `thermostat_state` | string | No | NULL | Enum | active\|idle |
| `day_night` | string | No | NULL | Enum | day\|night |
| `weather_conditions` | string | No | NULL | Pipe-separated | sunny\|cloudy\|raining\|snowing\|windy |
| `raw_response` | text | No | NULL | Valid JSON | Full API response for debugging |
| `created_at` | datetime | Auto | Current time | ISO 8601 with TZ | When record was inserted |

#### Validation Rules
- **Temperature ranges**:
  - Indoor (hue_sensor, nest_thermostat): 0-40°C
  - Outdoor (weather_api): -40-50°C
  - Out-of-range values flagged but not rejected
- **Device ID format**: Must match `^[a-z_]+:[a-zA-Z0-9_-]+$`
- **Duplicate detection**: Unique constraint on (device_id, timestamp)
- **Required fields**: timestamp, device_id, temperature_celsius, location, device_type
- **Timestamp**: Must include timezone information

#### Relationships
- No foreign keys in MVP (single table design for simplicity)
- Future: Could add `devices` table for metadata normalization

#### State Transitions
- None (readings are immutable snapshots)

---

## Database Schema Design

### Table: `readings`

```sql
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    device_id TEXT NOT NULL,
    temperature_celsius REAL NOT NULL,
    location TEXT NOT NULL,
    device_type TEXT NOT NULL CHECK(device_type IN ('hue_sensor', 'nest_thermostat', 'weather_api')),
    
    -- Optional metadata
    humidity_percent REAL CHECK(humidity_percent IS NULL OR (humidity_percent >= 0 AND humidity_percent <= 100)),
    battery_level INTEGER CHECK(battery_level IS NULL OR (battery_level >= 0 AND battery_level <= 100)),
    signal_strength INTEGER CHECK(signal_strength IS NULL OR (signal_strength >= 0 AND signal_strength <= 100)),
    thermostat_mode TEXT CHECK(thermostat_mode IS NULL OR thermostat_mode IN ('heating', 'cooling', 'off', 'away')),
    thermostat_state TEXT CHECK(thermostat_state IS NULL OR thermostat_state IN ('active', 'idle')),
    day_night TEXT CHECK(day_night IS NULL OR day_night IN ('day', 'night')),
    weather_conditions TEXT,
    raw_response TEXT,
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(device_id, timestamp),
    CHECK(temperature_celsius >= -40 AND temperature_celsius <= 50)
);

-- Indexes for time-series queries
CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_readings_device_id ON readings(device_id);
CREATE INDEX IF NOT EXISTS idx_readings_device_timestamp ON readings(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_readings_location ON readings(location);
```

### Performance Considerations
- **Indexes**: Cover common query patterns (time ranges, per-device, by location)
- **No foreign keys**: Simplifies schema, acceptable for single-table design
- **AUTOINCREMENT**: Ensures IDs never reused even after deletions
- **Composite unique constraint**: Prevents duplicate readings
- **CHECK constraints**: Enforce data quality at database level

### Storage Estimates
- **Row size**: ~200-500 bytes (depending on optional fields)
- **Daily volume**: ~5-10 devices × 288 readings/day = 1,440-2,880 readings/day
- **Daily storage**: ~0.3-1.5 MB/day
- **Annual storage**: ~100-500 MB/year (well within constraints)

---

## Data Validation Logic

### Temperature Validation
```python
def validate_temperature(temp: float, device_type: str) -> tuple[bool, str]:
    """
    Validate temperature reading against expected ranges.
    Returns (is_valid, message)
    """
    if device_type == 'weather_api':
        if -40 <= temp <= 50:
            return True, "OK"
        return False, f"Weather temp {temp}°C outside range [-40, 50]"
    else:  # Indoor sensors
        if 0 <= temp <= 40:
            return True, "OK"
        return False, f"Indoor temp {temp}°C outside range [0, 40]"
```

### Device ID Validation
```python
import re

DEVICE_ID_PATTERN = re.compile(r'^[a-z_]+:[a-zA-Z0-9_-]+$')

def validate_device_id(device_id: str) -> tuple[bool, str]:
    """
    Validate composite device ID format.
    Returns (is_valid, message)
    """
    if not DEVICE_ID_PATTERN.match(device_id):
        return False, f"Invalid device_id format: {device_id}"
    
    source_type, _ = device_id.split(':', 1)
    valid_sources = ['hue', 'nest', 'weather']
    if source_type not in valid_sources:
        return False, f"Unknown source type: {source_type}"
    
    return True, "OK"
```

### Duplicate Detection
```python
def check_duplicate(device_id: str, timestamp: datetime, db_connection) -> bool:
    """
    Check if reading already exists for device at timestamp.
    Returns True if duplicate exists.
    """
    cursor = db_connection.execute(
        "SELECT COUNT(*) FROM readings WHERE device_id = ? AND timestamp = ?",
        (device_id, timestamp)
    )
    count = cursor.fetchone()[0]
    return count > 0
```

---

# Data Dictionary: Home Temperature Monitoring

| Term | Definition | Example |
|------|------------|---------|
| **Reading** | Single temperature measurement at a point in time | 21.5°C at 2025-11-18T14:30:00+00:00 |
| **Device ID** | Composite identifier for data source | `hue:sensor_abc123` |
| **Source Type** | Category of data source | hue, nest, weather |
| **Location** | Physical location of sensor | "living_room", "bedroom", "outside" |
| **Device Type** | Specific type of device | hue_sensor, nest_thermostat, weather_api |
| **Metadata** | Optional contextual information | humidity, battery, weather conditions |
| **Timestamp** | When reading was taken (not inserted) | ISO 8601 with timezone |
| **Created At** | When record was inserted into database | ISO 8601 with timezone |

---

## Configuration Options

### config.yaml
- collection.interval_seconds: How often to collect readings (seconds)
- collection.retry_attempts: Number of retry attempts for API calls
- collection.retry_backoff_base: Base seconds for exponential backoff
- storage.database_path: Path to SQLite database file
- logging.level: Log verbosity
- validation.indoor_temp_min/max: Indoor temperature range
- validation.outdoor_temp_min/max: Outdoor temperature range
- collectors: Collector-specific settings

---

## Phase 1 Completion

✅ **All entities defined with fields and validation**  
✅ **Database schema designed with constraints and indexes**  
✅ **Validation logic specified**  
✅ **Data dictionary documented**  
✅ **Performance considerations addressed**  
✅ **Storage estimates calculated**

**Status**: Ready to proceed to API contracts generation
