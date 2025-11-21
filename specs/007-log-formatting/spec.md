# Spec 007: Structured JSON Log Formatting

**Status:** Specification  
**Date:** 2025-11-21  
**Owner:** System Architecture  
**Phase:** 8+ (Integration Testing & Analysis)

## Overview

Implement structured JSON logging across all collectors and background processes to enable:
- Easy parsing and filtering of logs
- Integration with Console.app and standard log viewers
- Automated metrics extraction (timing, error rates, retry stats)
- Analysis and reporting for 24-hour reliability tests
- Debugging and troubleshooting with rich metadata

## Current State

**Problems:**
- Plain text logs mixed with Python logging output
- Inconsistent formatting between collectors
- No structured metadata (duration, counts, errors)
- Manual parsing required to extract statistics
- Hard to filter by component or time range in 24h tests

**Example of current logs:**
```
2025-11-21 06:12:25,196 - __main__ - INFO - Successfully connected to Hue Bridge
2025-11-21 06:12:25,196 - __main__ - INFO - Starting collection cycle...
2025-11-21 06:12:25,287 - __main__ - INFO - API optimization: fetched all sensors in 37ms
2025-11-21 06:12:25,288 - __main__ - INFO - ✓ Collected: Utility = 21.42°C
[2025-11-21 06:12:25] Hue collection completed successfully
```

## Proposed Solution

### JSON Log Format

Each log line is valid JSON with these fields:

**Required:**
- `timestamp` (ISO 8601): `"2025-11-21T06:15:00.123Z"`
- `level` (string): `"INFO" | "WARNING" | "ERROR" | "SUCCESS" | "DEBUG"`
- `component` (string): `"hue_collector" | "amazon_collector" | "runner_script" | "storage_manager"`
- `message` (string): Human-readable description of the event

**Optional (context-dependent):**
- `duration_ms` (integer): How long operation took
- `readings_count` (integer): Number of readings collected
- `errors` (array): List of errors that occurred
- `error_code` (string): Machine-readable error identifier
- `device_ids` (array): List of device identifiers
- `devices` (array): Device details with readings
- `cycle_id` (string): Unique identifier for collection cycle
- `bridge_ip` (string): Bridge IP address
- `sensor_count` (integer): Total sensors discovered
- `temperature_sensors` (integer): Temperature-capable sensors
- `status` (string): Operation status (`"success" | "failure" | "partial"`)
- `attempt` (integer): Retry attempt number
- `max_retries` (integer): Maximum retry attempts
- `next_retry_ms` (integer): Milliseconds until next retry
- `duplicates` (integer): Number of duplicate readings
- `battery` (integer): Battery level (0-100)
- `temp` (number): Temperature value
- `metadata` (object): Any additional context-specific data

### Example Log Entries

#### 1. Collection Start (Runner Script)
```json
{
  "timestamp": "2025-11-21T06:15:00.000Z",
  "level": "INFO",
  "component": "runner_script",
  "message": "Starting Hue collection cycle",
  "cycle_id": "hue-20251121-061500"
}
```

#### 2. Bridge Connection
```json
{
  "timestamp": "2025-11-21T06:15:01.234Z",
  "level": "INFO",
  "component": "hue_collector",
  "message": "Connected to Hue Bridge",
  "bridge_ip": "192.168.1.105",
  "duration_ms": 1234
}
```

#### 3. Sensor Discovery
```json
{
  "timestamp": "2025-11-21T06:15:02.500Z",
  "level": "INFO",
  "component": "hue_collector",
  "message": "Discovered temperature sensors",
  "sensor_count": 26,
  "temperature_sensors": 2,
  "device_ids": ["Utility", "Hall"],
  "duration_ms": 200
}
```

#### 4. Collection Success
```json
{
  "timestamp": "2025-11-21T06:15:03.800Z",
  "level": "SUCCESS",
  "component": "hue_collector",
  "message": "Collection completed successfully",
  "readings_count": 2,
  "devices": [
    {"name": "Utility", "temp": 21.42, "battery": 100},
    {"name": "Hall", "temp": 20.40, "battery": 100}
  ],
  "duration_ms": 800,
  "total_cycle_ms": 3800,
  "status": "success"
}
```

#### 5. Retry Attempt
```json
{
  "timestamp": "2025-11-21T06:20:01.100Z",
  "level": "WARNING",
  "component": "hue_collector",
  "message": "Bridge connection timeout, retrying...",
  "error_code": "connection_timeout",
  "attempt": 1,
  "max_retries": 3,
  "next_retry_ms": 2000
}
```

#### 6. Error
```json
{
  "timestamp": "2025-11-21T06:25:02.400Z",
  "level": "ERROR",
  "component": "amazon_collector",
  "message": "Failed to retrieve device credentials",
  "error_code": "authentication_failed",
  "device": "amazon_aqm_001",
  "error_details": "Invalid session token"
}
```

#### 7. Database Storage
```json
{
  "timestamp": "2025-11-21T06:15:04.200Z",
  "level": "INFO",
  "component": "storage_manager",
  "message": "Readings stored",
  "readings_count": 2,
  "duplicates": 0,
  "errors": 0,
  "duration_ms": 400
}
```

#### 8. Collection End (Success)
```json
{
  "timestamp": "2025-11-21T06:15:05.000Z",
  "level": "INFO",
  "component": "runner_script",
  "message": "Collection cycle complete",
  "cycle_id": "hue-20251121-061500",
  "status": "success",
  "total_duration_ms": 5000,
  "readings_stored": 2
}
```

#### 9. Collection End (Failure)
```json
{
  "timestamp": "2025-11-21T06:20:10.000Z",
  "level": "ERROR",
  "component": "runner_script",
  "message": "Collection cycle failed",
  "cycle_id": "amazon-20251121-062010",
  "status": "failure",
  "error_code": "bridge_unreachable",
  "total_duration_ms": 9500
}
```

## Implementation Timeline

### Phase 1: Specification (THIS ITEM)
- [x] Define JSON schema
- [x] Document all field types
- [x] Create real-world examples
- [x] Define filtering patterns
- [ ] Get stakeholder approval

### Phase 2: Collector Implementation
- [ ] Create structured logging wrapper in `source/utils/structured_logger.py`
- [ ] Update `source/collectors/hue_collector.py` to emit JSON
- [ ] Update `source/collectors/amazon_aqm_collector_main.py` to emit JSON
- [ ] Add timing measurements to collectors
- [ ] Capture device/error metadata

### Phase 3: Runner Script Updates
- [ ] Modify `scripts/collectors-hue-runner.sh`
- [ ] Modify `scripts/collectors-amazon-runner.sh`
- [ ] Ensure JSON output is preserved through piping
- [ ] Add cycle start/end logging at runner level
- [ ] Handle line buffering for real-time viewing

### Phase 4: Log Parser Utility
- [ ] Create `source/utils/log_parser.py`
- [ ] Implement filtering (level, component, time range)
- [ ] Implement statistics aggregation
- [ ] Create error analysis functions
- [ ] Generate human-readable reports

### Phase 5: Makefile Integration
- [ ] Add `make log-view` (tail with colors)
- [ ] Add `make log-errors` (filter errors only)
- [ ] Add `make log-stats` (summary statistics)
- [ ] Add `make log-json` (raw JSON output)
- [ ] Add `make log-filter` (advanced filtering)

## Usage Examples

### After Implementation

**View all logs in real-time:**
```bash
make log-view
```

**View only errors:**
```bash
make log-errors
```

**Get statistics:**
```bash
make log-stats
# Output:
# Total cycles: 288
# Success rate: 98.6%
# Average cycle time: 5.2s
# Min/Max: 4.8s / 12.3s
# P95: 6.1s
# Errors: 4 (1.4%)
# Retries: 12 (4.2%)
```

**Filter by component:**
```bash
tail -f logs/hue_scheduled.log | jq 'select(.component == "hue_collector")'
```

**Extract retry metrics:**
```bash
make log-json | jq '.[] | select(.level=="WARNING") | select(.message | contains("retry"))'
```

**View in Console.app:**
```bash
open -a Console logs/hue_scheduled.log
```

**Generate test report:**
```bash
make log-stats > 24h_test_report.txt
```

## Benefits for 24-Hour Testing

1. **Easy Error Analysis**: Quickly identify all errors and their patterns
2. **Performance Metrics**: Track timing trends across 288 cycles
3. **Retry Tracking**: See which devices have issues
4. **Data Loss Detection**: Compare expected vs actual readings
5. **Automated Validation**: Extract pass/fail criteria automatically
6. **Root Cause Analysis**: Rich metadata helps debug issues
7. **Trend Analysis**: Identify performance degradation over time

## Console.app Integration

With structured JSON logs, macOS Console.app can:
- Parse and display as searchable table
- Filter by level (errors, warnings only)
- Filter by component (hue vs amazon)
- Search by message text
- Group by timestamp or component
- Show performance trends via duration_ms field

## Backwards Compatibility

- Runner scripts will emit JSON only (not mixed formats)
- Old plain-text logs will be deprecated
- Log parser will handle both formats during transition
- Database schema unchanged (logs are independent)

## Testing Strategy

1. **Unit Tests**: Test log parser filtering and aggregation
2. **Integration Tests**: Verify log output from collectors
3. **Manual Testing**: View logs in Console.app
4. **24h Test**: Generate report from real 24-hour run
5. **Validation**: Verify all expected log types appear

## Success Criteria

- [x] All log entries are valid JSON
- [ ] Parser can filter by any field
- [ ] Statistics extracted in <100ms from large logs
- [ ] Console.app reads logs without errors
- [ ] 24h test report generated automatically
- [ ] <5% performance overhead vs current logging

## References

- macOS Unified Logging: https://developer.apple.com/documentation/os/logging
- JSON Schema: https://json-schema.org/
- jq manual: https://stedolan.github.io/jq/
- Python logging: https://docs.python.org/3/library/logging.html

## Notes

- Use ISO 8601 timestamps for consistency across systems
- All timestamps in UTC (Z suffix)
- Millisecond precision for duration measurements
- Error codes should be machine-readable identifiers
- Messages should be user-friendly (not cryptic)
- Include context but avoid excessive verbosity
