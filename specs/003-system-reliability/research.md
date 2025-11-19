# Phase 0: Research - System Reliability and Health Improvements

**Feature**: 003-system-reliability  
**Date**: 2025-11-19  
**Purpose**: Resolve technical unknowns and establish best practices for reliability improvements

---

## Research Task 1: SQLite Concurrency - WAL Mode vs Default Journal

### Decision
Enable **Write-Ahead Logging (WAL) mode** for the SQLite database to support concurrent reads during writes and reduce lock contention.

### Rationale
- **Problem**: Current default journal mode (`DELETE`) locks the entire database during writes, causing "database is locked" errors when multiple collection processes run simultaneously
- **WAL Benefits**:
  - Readers don't block writers, writers don't block readers
  - Only write-write conflicts cause locks (much rarer)
  - Better performance for write-heavy workloads
  - Database integrity maintained with automatic checkpointing
- **Quick & Dirty Alignment**: WAL is a configuration change (`PRAGMA journal_mode=WAL`), not a complex architectural addition
- **Trade-offs Accepted**: WAL creates `-wal` and `-shm` files alongside database (acceptable), requires SQLite 3.7.0+ (we have 3.11+)

### Alternatives Considered
1. **Connection Pooling**: More complex, requires additional library (e.g., `sqlalchemy`), violates "quick and dirty" principle
2. **File Locking with `flock`**: Custom solution, error-prone, doesn't solve read-during-write scenario
3. **Queue-Based Writes**: Significant architectural change, over-engineered for 2-10 sensors

### Implementation Details
```python
# In DatabaseManager.__init__() or init_schema()
self.conn.execute("PRAGMA journal_mode=WAL")
self.conn.commit()
```

**References**:
- [SQLite WAL Mode Documentation](https://www.sqlite.org/wal.html)
- [Python sqlite3 concurrency patterns](https://docs.python.org/3/library/sqlite3.html#sqlite3-controlling-transactions)

---

## Research Task 2: Database Retry Logic - Exponential Backoff Strategy

### Decision
Implement exponential backoff with **3 attempts, base delay of 1 second, multiplier of 2** for transient database lock errors.

### Rationale
- **Problem**: Even with WAL mode, write-write conflicts can still cause temporary locks
- **Exponential Backoff Benefits**:
  - First retry at 1s catches brief locks (e.g., checkpoint operations)
  - Second retry at 2s handles slightly longer operations
  - Total max wait time: 3s (1s + 2s), acceptable for 5-minute collection intervals
  - Avoids retry storms if multiple processes retry simultaneously
- **Alignment with Existing**: Constitution already specifies 3 attempts with exponential backoff for API calls; database retry uses same pattern for consistency

### Alternatives Considered
1. **Fixed Delay Retry**: Simpler but can cause synchronized retry storms
2. **Jittered Backoff**: More sophisticated but over-engineered for local-only execution with 2-10 sensors
3. **Infinite Retry**: Risk of deadlock or indefinite hangs

### Implementation Details
```python
def insert_temperature_reading(self, reading: dict, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            # ... insert logic ...
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait_time)
                continue
            raise
```

**References**:
- [Exponential backoff best practices](https://en.wikipedia.org/wiki/Exponential_backoff)
- [SQLite busy timeout](https://www.sqlite.org/c3ref/busy_timeout.html)

---

## Research Task 3: Hue API Optimization - Sensor-Only vs Full Configuration Fetch

### Decision
Fetch **only sensor data** using `/api/<key>/sensors` endpoint instead of full bridge configuration via `bridge.get_api()`.

### Rationale
- **Current State**: `bridge.get_api()` returns entire bridge state (~50-200KB depending on setup):
  - All lights and their states
  - Groups and scenes
  - Schedules and rules
  - Configuration settings
  - Resource links
- **Optimized Approach**: Direct HTTP GET to `/api/<key>/sensors` returns only sensor data (~5-10KB)
- **Bandwidth Savings**: 80-95% reduction in response payload size
- **Speed Impact**: Network transfer time reduced proportionally; local network means smaller absolute gains but still 30%+ faster due to JSON parsing overhead
- **Backward Compatibility**: Sensor data structure identical in both responses; no breaking changes

### Alternatives Considered
1. **Caching Full Configuration**: Reduces network calls but adds complexity for cache invalidation when sensors added/removed
2. **Individual Sensor Queries**: `/api/<key>/sensors/<id>` per sensor reduces payload but increases request count (worse for multi-sensor setups)
3. **No Optimization**: Simpler but wastes bandwidth and slows collection unnecessarily

### Implementation Details
```python
# Current (full config):
api_data = bridge.get_api()
sensors = api_data['sensors']

# Optimized (sensors only):
import requests
response = requests.get(f"http://{bridge_ip}/api/{api_key}/sensors")
sensors = response.json()
```

**Measurement Plan**:
- Baseline: Measure `bridge.get_api()` response size and time
- Optimized: Measure `/api/<key>/sensors` response size and time
- Verify: >30% cycle time reduction, >50% payload reduction

**References**:
- [Hue API Documentation - Sensors](https://developers.meethue.com/develop/hue-api/lights-api/)
- [phue library source code](https://github.com/studioimaginaire/phue)

---

## Research Task 4: Log Rotation - RotatingFileHandler Best Practices

### Decision
Use Python's built-in **`logging.handlers.RotatingFileHandler`** with 10MB max file size, 5 backup files, UTF-8 encoding.

### Rationale
- **Problem**: Long-running collection processes (30+ days) generate unbounded logs, risking disk exhaustion
- **RotatingFileHandler Benefits**:
  - Standard library solution (no new dependencies)
  - Automatic rotation when size threshold reached
  - Automatic deletion of oldest backups
  - Thread-safe for concurrent writers
  - Configurable via existing `config.yaml`
- **Size Calculation**:
  - ~500 log entries/hour (sensors + retries + errors)
  - ~200 bytes/entry average
  - ~100KB/hour → ~2.4MB/day
  - 10MB = ~4 days of logs per file
  - 5 backups = 20 days history = 60MB total max disk usage
- **Alignment**: Constitution allows "quick and dirty" solutions; stdlib handler fits perfectly

### Alternatives Considered
1. **`TimedRotatingFileHandler`**: Rotates by time (daily/weekly) but doesn't bound disk usage if collection frequency increases
2. **External Log Management** (e.g., `logrotate`): Platform-specific, requires system configuration, violates "local execution only" constraint
3. **Manual Log Deletion**: Error-prone, requires cron job or manual intervention

### Implementation Details
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    filename='logs/hue_collection.log',
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
```

**Configuration Schema**:
```yaml
logging:
  level: "INFO"
  enable_file_logging: true
  log_file_path: "logs/hue_collection.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

**References**:
- [Python logging.handlers documentation](https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler)
- [Logging cookbook - rotation](https://docs.python.org/3/howto/logging-cookbook.html#using-file-rotation)

---

## Research Task 5: Health Check Design - Command Structure and Validation Scope

### Decision
Create **`source/verify_setup.py`** script that validates configuration, secrets, database access, and Hue Bridge connectivity in sequence, reporting pass/fail for each component with actionable error messages.

### Rationale
- **Problem**: Configuration errors discovered during collection waste time and create confusing logs; no pre-flight validation exists
- **Health Check Scope**:
  1. **Configuration Validation**: `config.yaml` exists, is valid YAML, has required keys
  2. **Secrets Validation**: `secrets.yaml` exists, has Hue API key
  3. **Database Access**: Can create connection, write test record, delete it
  4. **Bridge Connectivity**: Can connect to bridge, API key authenticates, sensors discoverable
- **Exit Codes for Automation**:
  - `0`: All checks passed
  - `1`: One or more checks failed
  - `2`: Critical error (e.g., Python import failure)
- **Alignment**: Supports "scheduled/automated collection" (in scope) by enabling pre-run validation in cron jobs or systemd timers

### Alternatives Considered
1. **Integrated into Collector**: Less separation of concerns, harder to run independently
2. **Separate Health Checks per Component**: More modular but requires multiple commands (worse UX)
3. **Monitoring/Alerting System**: Over-engineered for local-only execution; out of scope

### Implementation Details
```python
#!/usr/bin/env python3
"""
System Health Check for Home Temperature Monitoring

Validates:
- Configuration files (config.yaml, secrets.yaml)
- Database write access
- Hue Bridge connectivity and authentication
- Sensor discovery

Exit codes:
    0 = All checks passed
    1 = One or more checks failed
    2 = Critical error
"""

def check_config():
    """Validate config.yaml exists and has required keys."""
    # ... implementation ...

def check_secrets():
    """Validate secrets.yaml exists and has Hue API key."""
    # ... implementation ...

def check_database():
    """Validate database write access."""
    # ... implementation ...

def check_hue_bridge():
    """Validate Hue Bridge connectivity and sensor discovery."""
    # ... implementation ...

def main():
    checks = [
        ("Configuration", check_config),
        ("Secrets", check_secrets),
        ("Database", check_database),
        ("Hue Bridge", check_hue_bridge),
    ]
    
    results = []
    for name, check_fn in checks:
        try:
            success, message = check_fn()
            results.append((name, success, message))
        except Exception as e:
            results.append((name, False, str(e)))
    
    # Print results
    # Exit with appropriate code
```

**Usage**:
```bash
# Run health check before starting continuous collection
python source/verify_setup.py && python source/collectors/hue_collector.py --continuous
```

**References**:
- [Health check pattern for monitoring systems](https://microservices.io/patterns/observability/health-check-api.html)
- [Unix exit codes](https://tldp.org/LDP/abs/html/exitcodes.html)

---

## Research Task 6: Context Manager for Database Connections

### Decision
Implement **`__enter__` and `__exit__` methods** in `DatabaseManager` to support `with` statement for automatic resource cleanup.

### Rationale
- **Problem**: Current code requires manual `db.close()` calls; risk of leaked connections if exceptions occur
- **Context Manager Benefits**:
  - Automatic connection cleanup even on errors
  - Pythonic pattern for resource management
  - Reduces code in collectors (no explicit close needed)
  - Ensures WAL checkpoint flushed on close
- **Implementation Simplicity**: Add 6 lines of code to existing `DatabaseManager` class

### Alternatives Considered
1. **Manual Close Everywhere**: Error-prone, violates DRY
2. **Singleton Connection**: Keeps connection open indefinitely, risks corruption on crashes
3. **Finalizer (`__del__`)**: Unreliable timing, not guaranteed to run

### Implementation Details
```python
class DatabaseManager:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # Don't suppress exceptions
```

**Usage**:
```python
# Before:
db = DatabaseManager()
try:
    db.insert_temperature_reading(reading)
finally:
    db.close()

# After:
with DatabaseManager() as db:
    db.insert_temperature_reading(reading)
```

**References**:
- [Python context managers](https://docs.python.org/3/reference/datamodel.html#context-managers)
- [PEP 343 - The "with" Statement](https://www.python.org/dev/peps/pep-0343/)

---

## Summary of Research Findings

| Research Area | Solution | Key Benefit | Complexity |
|---------------|----------|-------------|------------|
| Database Concurrency | WAL Mode | Eliminate most lock errors | Low (1 line) |
| Retry Logic | Exponential Backoff (3x, 2^n) | Handle transient locks gracefully | Low (10 lines) |
| API Optimization | Sensors-only endpoint | 50%+ bandwidth reduction | Low (5 lines) |
| Log Management | RotatingFileHandler | Bounded disk usage (60MB max) | Low (stdlib) |
| Health Check | Pre-flight validation script | Catch config errors early | Medium (new file) |
| Resource Cleanup | Context Manager | Prevent connection leaks | Low (6 lines) |

**All research complete. Ready for Phase 1: Data Model & Contracts.**
