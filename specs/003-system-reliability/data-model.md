# Data Model: System Reliability and Health Improvements

**Feature**: 003-system-reliability  
**Date**: 2025-11-19  
**Status**: Phase 1

---

## Overview

This feature introduces **operational entities** for reliability and health monitoring, not new data storage entities. The core `TemperatureReading` entity remains unchanged. Instead, this document defines configuration entities, runtime state objects, and health check results.

---

## Entity 1: Database Configuration

**Purpose**: SQLite-specific configuration for WAL mode and retry behavior  
**Lifecycle**: Loaded at startup, applied during database initialization  
**Storage**: `config/config.yaml` under `storage` section

### Fields

| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| `database_path` | string | Yes | `data/readings.db` | Valid path | SQLite database file location |
| `enable_wal_mode` | boolean | Yes | `true` | - | Enable Write-Ahead Logging |
| `wal_checkpoint_interval` | integer | No | `1000` | > 0 | Rows between checkpoints (0 = auto) |
| `retry_max_attempts` | integer | Yes | `3` | 1-10 | Max retry attempts for locked DB |
| `retry_base_delay` | float | Yes | `1.0` | > 0 | Base delay in seconds for exponential backoff |
| `busy_timeout_ms` | integer | No | `5000` | >= 0 | SQLite busy timeout (milliseconds) |

### Validation Rules

```python
def validate_database_config(config: dict) -> list[str]:
    """Validate database configuration section."""
    errors = []
    
    if not config.get('database_path'):
        errors.append("database_path is required")
    
    if config.get('retry_max_attempts', 3) < 1:
        errors.append("retry_max_attempts must be >= 1")
    
    if config.get('retry_base_delay', 1.0) <= 0:
        errors.append("retry_base_delay must be > 0")
    
    return errors
```

### Example Configuration

```yaml
storage:
  database_path: "data/readings.db"
  enable_wal_mode: true
  wal_checkpoint_interval: 1000
  retry_max_attempts: 3
  retry_base_delay: 1.0
  busy_timeout_ms: 5000
```

---

## Entity 2: Log Rotation Configuration

**Purpose**: Define log file rotation parameters  
**Lifecycle**: Loaded at startup, applied during logging setup  
**Storage**: `config/config.yaml` under `logging` section

### Fields

| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| `level` | string | Yes | `INFO` | DEBUG\|INFO\|WARNING\|ERROR\|CRITICAL | Logging verbosity |
| `enable_file_logging` | boolean | Yes | `true` | - | Enable file logging (vs console only) |
| `log_file_path` | string | Yes* | `logs/hue_collection.log` | Valid path | Log file location |
| `max_bytes` | integer | Yes* | `10485760` | > 0 | Max file size before rotation (bytes) |
| `backup_count` | integer | Yes* | `5` | >= 0 | Number of backup files to keep |
| `encoding` | string | No | `utf-8` | Valid encoding | Log file encoding |

*Required if `enable_file_logging` is `true`

### Validation Rules

```python
def validate_logging_config(config: dict) -> list[str]:
    """Validate logging configuration section."""
    errors = []
    
    valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
    if config.get('level', 'INFO').upper() not in valid_levels:
        errors.append(f"Invalid log level: {config.get('level')}")
    
    if config.get('enable_file_logging', False):
        if not config.get('log_file_path'):
            errors.append("log_file_path required when file logging enabled")
        if not config.get('max_bytes'):
            errors.append("max_bytes required when file logging enabled")
        if config.get('backup_count') is None:
            errors.append("backup_count required when file logging enabled")
    
    return errors
```

### Example Configuration

```yaml
logging:
  level: "INFO"
  enable_file_logging: true
  log_file_path: "logs/hue_collection.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
  encoding: "utf-8"
```

### Disk Usage Calculation

```python
def calculate_max_log_disk_usage(config: dict) -> int:
    """
    Calculate maximum disk usage for logs.
    
    Returns: Maximum bytes consumed by log files
    """
    max_bytes = config.get('max_bytes', 10485760)
    backup_count = config.get('backup_count', 5)
    
    # Active file + backups
    return max_bytes * (1 + backup_count)

# Example: 10MB * (1 + 5) = 60MB total
```

---

## Entity 3: Health Check Result

**Purpose**: Report system component validation status  
**Lifecycle**: Created on-demand when health check runs, not persisted  
**Storage**: Runtime only (printed to console, returned as exit code)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `component` | string | Yes | Component name (e.g., "Configuration", "Database") |
| `status` | string | Yes | "PASS" or "FAIL" |
| `message` | string | Yes | Human-readable status message |
| `details` | dict | No | Additional diagnostic information |
| `timestamp` | string (ISO 8601) | Yes | When check was performed |
| `duration_ms` | integer | No | Check execution time in milliseconds |

### Status Enumeration

```python
from enum import Enum

class HealthStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
```

### Component Types

```python
HEALTH_COMPONENTS = {
    'configuration': {
        'name': 'Configuration',
        'description': 'Validates config.yaml exists and has required keys',
    },
    'secrets': {
        'name': 'Secrets',
        'description': 'Validates secrets.yaml exists and has Hue API key',
    },
    'database': {
        'name': 'Database',
        'description': 'Validates database write access and schema',
    },
    'hue_bridge': {
        'name': 'Hue Bridge',
        'description': 'Validates bridge connectivity and sensor discovery',
    },
}
```

### Example Health Check Result

```python
{
    'component': 'Database',
    'status': 'PASS',
    'message': 'Database write test successful',
    'details': {
        'database_path': 'data/readings.db',
        'wal_mode': 'enabled',
        'writable': True,
    },
    'timestamp': '2025-11-19T10:30:00+00:00',
    'duration_ms': 15,
}
```

### Console Output Format

```
============================================================
🏥 SYSTEM HEALTH CHECK
============================================================

✅ Configuration: PASS
   Config file valid, all required keys present

✅ Secrets: PASS
   Hue API key found

✅ Database: PASS
   Database write test successful (WAL mode enabled)

✅ Hue Bridge: PASS
   Connected to bridge 192.168.1.105, 2 sensors discovered

============================================================
📊 OVERALL STATUS: HEALTHY
All 4 checks passed in 0.8s
============================================================
```

---

## Entity 4: Database Retry State

**Purpose**: Track retry attempts for transient database errors  
**Lifecycle**: Created per insert operation, discarded after success or max retries  
**Storage**: Runtime only (in-memory during operation)

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `attempt_number` | integer | Current attempt (1-indexed) |
| `max_attempts` | integer | Maximum attempts allowed |
| `last_error` | string | Error message from previous attempt |
| `wait_time` | float | Delay before next retry (seconds) |
| `total_elapsed` | float | Total time spent retrying (seconds) |

### State Transitions

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ├─→ [Attempt 1] ─┬─→ SUCCESS ──→ DONE ✓
       │                 │
       │                 └─→ LOCKED ──→ Wait 1s
       │                                   │
       ├─→ [Attempt 2] ─┬─→ SUCCESS ──→ DONE ✓
       │                 │
       │                 └─→ LOCKED ──→ Wait 2s
       │                                   │
       └─→ [Attempt 3] ─┬─→ SUCCESS ──→ DONE ✓
                         │
                         └─→ LOCKED ──→ FAIL ✗
```

### Implementation Example

```python
import time
import sqlite3

def insert_with_retry(conn, reading: dict, config: dict) -> bool:
    """
    Insert reading with exponential backoff retry.
    
    Returns:
        bool: True if successful, False if failed after max retries
    """
    max_attempts = config.get('retry_max_attempts', 3)
    base_delay = config.get('retry_base_delay', 1.0)
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Attempt insert
            keys = ', '.join(reading.keys())
            placeholders = ', '.join(['?' for _ in reading])
            sql = f"INSERT INTO readings ({keys}) VALUES ({placeholders})"
            conn.execute(sql, tuple(reading.values()))
            conn.commit()
            
            if attempt > 1:
                logger.info(f"Insert succeeded on attempt {attempt}")
            
            return True
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_attempts:
                wait_time = base_delay * (2 ** (attempt - 1))  # 1s, 2s, 4s
                logger.warning(
                    f"Database locked (attempt {attempt}/{max_attempts}), "
                    f"retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Insert failed after {attempt} attempts: {e}")
                raise
        
        except sqlite3.IntegrityError as e:
            # Duplicate or constraint violation - don't retry
            if "UNIQUE constraint failed" in str(e):
                logger.debug("Duplicate reading, skipping")
                return False
            raise
    
    return False
```

---

## Entity 5: Hue API Request Metadata

**Purpose**: Track API request size and timing for optimization measurement  
**Lifecycle**: Created per API request during collection cycle, logged for analysis  
**Storage**: Runtime only (logged to file for performance analysis)

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `request_type` | string | "full_config" or "sensors_only" |
| `endpoint` | string | API endpoint called |
| `request_time` | string (ISO 8601) | When request was made |
| `response_size_bytes` | integer | Size of response payload |
| `duration_ms` | integer | Request duration in milliseconds |
| `sensor_count` | integer | Number of sensors in response |

### Measurement Logging

```python
import time
import sys

def measure_api_request(request_type: str, endpoint: str, response_data: dict):
    """Log API request metrics for performance analysis."""
    
    response_size = sys.getsizeof(str(response_data))
    sensor_count = len(response_data.get('sensors', {})) if 'sensors' in response_data else len(response_data)
    
    metrics = {
        'request_type': request_type,
        'endpoint': endpoint,
        'request_time': datetime.now(timezone.utc).isoformat(),
        'response_size_bytes': response_size,
        'sensor_count': sensor_count,
    }
    
    logger.info(f"API Metrics: {request_type} - {response_size} bytes, {sensor_count} sensors")
    return metrics
```

### Before/After Comparison

```python
# Before (full config):
{
    'request_type': 'full_config',
    'endpoint': '/api/<key>',
    'response_size_bytes': 187456,  # ~180KB
    'duration_ms': 245,
    'sensor_count': 2,
}

# After (sensors only):
{
    'request_type': 'sensors_only',
    'endpoint': '/api/<key>/sensors',
    'response_size_bytes': 8192,  # ~8KB
    'duration_ms': 95,
    'sensor_count': 2,
}

# Improvement: 95.6% size reduction, 61% faster
```

---

## Data Flow: Health Check Execution

```
┌──────────────────┐
│  verify_setup.py │
└────────┬─────────┘
         │
         ├─→ [1] Load config.yaml
         │      ├─→ PASS: Required keys present
         │      └─→ FAIL: Missing keys or invalid YAML
         │
         ├─→ [2] Load secrets.yaml
         │      ├─→ PASS: Hue API key found
         │      └─→ FAIL: File missing or no API key
         │
         ├─→ [3] Test database write
         │      ├─→ Create connection
         │      ├─→ Enable WAL mode
         │      ├─→ INSERT test record
         │      ├─→ DELETE test record
         │      ├─→ PASS: All operations successful
         │      └─→ FAIL: Permission error, locked, or schema issue
         │
         └─→ [4] Test Hue Bridge connection
                ├─→ Connect to bridge IP
                ├─→ Authenticate with API key
                ├─→ Fetch sensors endpoint
                ├─→ PASS: Sensors discovered
                └─→ FAIL: Network error, auth error, or no sensors
```

---

## Configuration Schema Changes

### Before (current config.yaml)

```yaml
storage:
  database_path: "data/readings.db"
  enable_pooling: false

logging:
  level: "INFO"
  enable_file_logging: true
  log_file_path: "logs/hue_collection.log"
  max_bytes: 10485760
  backup_count: 5
```

### After (enhanced config.yaml)

```yaml
storage:
  database_path: "data/readings.db"
  enable_pooling: false
  # NEW: WAL mode settings
  enable_wal_mode: true
  wal_checkpoint_interval: 1000
  # NEW: Retry settings
  retry_max_attempts: 3
  retry_base_delay: 1.0
  busy_timeout_ms: 5000

logging:
  level: "INFO"
  enable_file_logging: true
  log_file_path: "logs/hue_collection.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
  encoding: "utf-8"  # NEW: Explicit encoding
```

---

## No Database Schema Changes

**Important**: This feature does **NOT** modify the `readings` table schema. The `TemperatureReading` entity from previous sprints remains unchanged. All improvements are operational (WAL mode, retry logic, logging, health checks) rather than structural.

---

## Validation Summary

| Entity | Validation Type | Rules |
|--------|----------------|-------|
| **Database Configuration** | Type & Range | `retry_max_attempts` 1-10, `retry_base_delay` > 0 |
| **Log Rotation Configuration** | Required Fields | `log_file_path`, `max_bytes`, `backup_count` if file logging enabled |
| **Health Check Result** | Enum | `status` must be "PASS" or "FAIL" |
| **Database Retry State** | Logic | Exponential backoff: wait_time = base_delay * 2^(attempt-1) |
| **API Request Metadata** | Measurement | Before/after comparison for 30%+ improvement verification |

---

## Phase 1 Completion

✅ **Operational entities defined (configuration, health check, retry state)**  
✅ **Validation rules specified for configuration sections**  
✅ **State transitions documented for retry logic**  
✅ **No database schema changes (backward compatible)**  
✅ **Measurement approach for API optimization defined**

**Status**: Ready to generate contracts and quickstart documentation.
