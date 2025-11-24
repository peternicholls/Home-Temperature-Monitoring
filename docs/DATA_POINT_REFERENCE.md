# Structured Data Points Reference

Instead of parsing verbose log messages, all information is captured as queryable data points in JSON logs.

## Hue Collector Data Points

### Sensor Offline
```json
{
  "message": "Sensor offline",
  "location": "Daylight",
  "device_id": "...",
  "reason": "unreachable"
}
```

### Temperature Data Missing
```json
{
  "message": "Temperature data missing",
  "location": "...",
  "device_id": "...",
  "reason": "no_temperature_state"
}
```

### Temperature Anomaly
```json
{
  "message": "Temperature anomaly detected",
  "temperature_celsius": 45.5,
  "location": "...",
  "device_id": "..."
}
```

### Collection Failed
```json
{
  "message": "Collection failed",
  "location": "...",
  "device_id": "...",
  "error_type": "...",
  "error_message": "..."
}
```

### Readings Stored
```json
{
  "message": "Readings stored",
  "readings_count": 2,
  "duplicates": 0,
  "errors": 0,
  "duration_ms": 5
}
```

## Amazon Collector Data Points

### Device Discovery Complete
```json
{
  "message": "Device discovery complete",
  "device_count": 1,
  "device_ids": ["..."],
  "discovery_duration_ms": 1234
}
```

### Collection Completed
```json
{
  "message": "Collection completed successfully",
  "cycle_duration_ms": 1629,
  "status": "success"
}
```

## Usage with LogParser

```bash
# View all warnings with their reasons
make log-stats

# Filter by specific reason
python source/utils/log_parser.py logs/hue_scheduled.log | grep "no_temperature_state"

# Check anomalies
python source/utils/log_parser.py logs/hue_scheduled.log | grep "Temperature anomaly"

# View errors with types
python source/utils/log_parser.py logs/hue_scheduled.log | grep "Collection failed"
```

## Benefits

- ✅ **Queryable**: Each data point is a separate field
- ✅ **Aggregatable**: `make log-stats` groups by reason/type
- ✅ **Machine-readable**: Parse with jq or custom tools
- ✅ **No text parsing**: Avoids regex failures
- ✅ **Complete context**: All relevant fields always present
