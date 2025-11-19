# Quickstart: System Reliability and Health Improvements

**Feature**: 003-system-reliability  
**Sprint**: 1.1  
**Date**: 2025-11-19

---

## What's New in Sprint 1.1

This sprint enhances the Home Temperature Monitoring system with **operational reliability improvements**:

1. **🔒 Database Concurrency Protection**: WAL mode + retry logic eliminates "database locked" errors
2. **⚡ Faster Collection Cycles**: Optimized Hue API calls reduce network overhead by 50%+
3. **📝 Automatic Log Rotation**: Bounded disk usage prevents log file growth issues
4. **✅ Health Check Command**: Pre-flight validation catches configuration errors before collection

**No schema changes required** - all improvements are backward compatible.

---

## Prerequisites

- **Completed Sprint 1.0** (002-hue-integration): Hue authentication and basic collection working
- **Python 3.11+**: Existing installation
- **Dependencies**: No new packages required (uses stdlib enhancements)

---

## Quick Setup (5 minutes)

### Step 1: Update Configuration

Add new settings to `config/config.yaml`:

```bash
# Open config file
nano config/config.yaml
```

Add these sections (or merge with existing):

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
  # NEW: Rotation settings
  max_bytes: 10485760  # 10MB
  backup_count: 5
  encoding: "utf-8"
```

**Or** copy the reference config:

```bash
cp specs/003-system-reliability/contracts/config-enhanced.yaml config/config.yaml
```

### Step 2: Verify Setup

Run the health check to validate everything is configured correctly:

```bash
python source/verify_setup.py
```

**Expected output**:

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

**If any checks fail**, see [Troubleshooting](#troubleshooting) below.

### Step 3: Test Enhanced Collection

Run a single collection cycle to verify improvements:

```bash
python source/collectors/hue_collector.py --collect-once
```

Check the logs to verify:

1. **WAL mode enabled**: `WAL mode enabled for database` message
2. **Faster collection**: Compare cycle time to previous runs (should be 30%+ faster)
3. **No database errors**: No "database locked" warnings

---

## Testing the Improvements

### Test 1: Concurrent Collection (Database Reliability)

Run two collection processes simultaneously to verify lock-free operation:

```bash
# Terminal 1
python source/collectors/hue_collector.py --collect-once

# Terminal 2 (run immediately after starting Terminal 1)
python source/collectors/hue_collector.py --collect-once
```

**Expected**: Both processes complete successfully without "database is locked" errors.

**Before Sprint 1.1**: One process would fail with database lock error.  
**After Sprint 1.1**: Both succeed (WAL mode allows concurrent reads during writes).

### Test 2: API Optimization (Speed Improvement)

Measure collection cycle time improvement:

```bash
# Time a collection cycle
time python source/collectors/hue_collector.py --collect-once
```

**Expected**: 30%+ faster than Sprint 1.0 baseline.

**To compare formally**, run the optimization comparison script:

```bash
# Edit contracts/hue-api-optimization-comparison.py with your bridge IP and API key
python specs/003-system-reliability/contracts/hue-api-optimization-comparison.py
```

### Test 3: Log Rotation

Generate enough logs to trigger rotation:

```bash
# Run continuous collection for a few hours
python source/collectors/hue_collector.py --continuous

# In another terminal, check log file sizes
ls -lh logs/
```

**Expected**:
- Active log: `hue_collection.log` (growing, max 10MB)
- Backups: `hue_collection.log.1` through `hue_collection.log.5`
- Total disk usage: ≤ 60MB (10MB × 6 files)

**Verify rotation**:

```bash
# Watch log directory
watch -n 5 'ls -lh logs/'
```

When `hue_collection.log` reaches 10MB, it rotates to `.log.1` and a new `.log` starts.

### Test 4: Health Check Before Production

Integrate health check into automated collection workflow:

```bash
# Run health check, only start collection if healthy
python source/verify_setup.py && python source/collectors/hue_collector.py --continuous
```

**Use in cron**:

```bash
# Add to crontab (edit with: crontab -e)
# Run every 5 minutes, only if system is healthy
*/5 * * * * cd /path/to/project && python source/verify_setup.py && python source/collectors/hue_collector.py --collect-once >> logs/cron.log 2>&1
```

---

## Configuration Reference

### Database Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `enable_wal_mode` | `true` | Enable Write-Ahead Logging for concurrent access |
| `wal_checkpoint_interval` | `1000` | Checkpoint every N writes (0 = auto) |
| `retry_max_attempts` | `3` | Max retry attempts for locked database |
| `retry_base_delay` | `1.0` | Base delay for exponential backoff (seconds) |
| `busy_timeout_ms` | `5000` | SQLite busy timeout (milliseconds) |

### Logging Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `max_bytes` | `10485760` | Max log file size before rotation (10MB) |
| `backup_count` | `5` | Number of backup files to keep |
| `encoding` | `utf-8` | Log file encoding |

---

## Usage Patterns

### Development Workflow

```bash
# 1. Health check
python source/verify_setup.py

# 2. Test collection
python source/collectors/hue_collector.py --collect-once

# 3. Start continuous collection
python source/collectors/hue_collector.py --continuous
```

### Production Deployment

```bash
# Use health check as pre-condition
if python source/verify_setup.py; then
    echo "System healthy, starting collection..."
    python source/collectors/hue_collector.py --continuous
else
    echo "System unhealthy, check logs"
    exit 1
fi
```

### Monitoring

```bash
# Watch active log
tail -f logs/hue_collection.log

# Check disk usage
du -sh logs/

# Count readings
sqlite3 data/readings.db "SELECT COUNT(*) FROM readings;"

# Check WAL mode
sqlite3 data/readings.db "PRAGMA journal_mode;"
```

---

## Troubleshooting

### Health Check Failures

#### ❌ Configuration: FAIL

**Symptom**: "Config file not found" or "Missing required sections"

**Fix**:

```bash
# Copy reference config
cp specs/003-system-reliability/contracts/config-enhanced.yaml config/config.yaml

# Or restore from backup
cp config/config.yaml.example config/config.yaml
```

#### ❌ Secrets: FAIL

**Symptom**: "Secrets file not found" or "Missing hue.api_key"

**Fix**:

```bash
# Re-run authentication
python source/collectors/hue_auth.py
```

#### ❌ Database: FAIL

**Symptom**: "Database error" or "Permission denied"

**Fix**:

```bash
# Ensure data directory exists and is writable
mkdir -p data
chmod 755 data

# Remove corrupted database (if necessary)
rm data/readings.db
```

#### ❌ Hue Bridge: FAIL

**Symptom**: "Bridge connection failed" or "No temperature sensors found"

**Fix**:

1. **Check network**: Ping bridge IP

   ```bash
   ping 192.168.1.105
   ```

2. **Verify API key**: Re-authenticate if needed

   ```bash
   python source/collectors/hue_auth.py
   ```

3. **Check sensors**: Ensure sensors are online in Hue app

### Database Locked Errors (Persistent)

If you still see "database is locked" errors after Sprint 1.1:

1. **Verify WAL mode enabled**:

   ```bash
   sqlite3 data/readings.db "PRAGMA journal_mode;"
   # Should output: wal
   ```

2. **Enable WAL manually** (if not automatic):

   ```bash
   sqlite3 data/readings.db "PRAGMA journal_mode=WAL;"
   ```

3. **Check file permissions**:

   ```bash
   ls -la data/
   # Ensure readings.db, .db-wal, .db-shm are writable
   ```

### Log Rotation Not Working

**Symptom**: Log file grows beyond 10MB, no rotation happening

**Check**:

1. **Configuration loaded**: Verify `max_bytes` in config.yaml
2. **File handler created**: Check logs for "Logging configured" message
3. **Disk space**: Ensure sufficient space for rotated files

**Fix**:

```bash
# Manually rotate logs
cd logs
mv hue_collection.log hue_collection.log.manual
# Restart collection, new log file will be created
```

### Slow Collection Cycles

**Symptom**: Collection still slow despite API optimization

**Diagnose**:

```bash
# Run comparison script
python specs/003-system-reliability/contracts/hue-api-optimization-comparison.py
```

**Possible causes**:

1. Network latency (check WiFi signal to bridge)
2. Bridge overloaded (too many lights/sensors)
3. Python environment issues (try fresh virtualenv)

---

## What's Next

After Sprint 1.1, the system is ready for:

- **Long-running production deployment** (30+ days without manual intervention)
- **Concurrent collection processes** (e.g., backup script running alongside main collection)
- **Automated scheduling** (cron jobs with health check pre-conditions)

**Next sprint candidates**:

1. **Google Nest Integration** (003-nest-integration)
2. **Weather API Collection** (004-weather-integration)
3. **Data Export for Analysis** (005-data-export)

---

## Success Metrics

After deploying Sprint 1.1, you should observe:

| Metric | Before Sprint 1.1 | After Sprint 1.1 | Target |
|--------|-------------------|------------------|--------|
| Database lock errors | Common | Zero | 0% error rate |
| Collection cycle time | ~800ms | ~500ms | 30%+ faster |
| Log disk usage | Unbounded | ≤60MB | Bounded |
| Configuration errors | Discovered during collection | Caught by health check | Pre-flight validation |
| Concurrent collection | Fails | Succeeds | 100% success |

**Verify success**:

```bash
# Run for 24 hours
python source/collectors/hue_collector.py --continuous

# Check logs for errors
grep -i "locked" logs/hue_collection.log
# Should return: 0 results

# Check disk usage
du -sh logs/
# Should be: ≤60MB
```

---

## Developer Notes

### Testing Changes in Isolation

```bash
# Test WAL mode only
sqlite3 data/readings.db "PRAGMA journal_mode=WAL;"

# Test retry logic only (disable WAL)
# Edit source/storage/manager.py, set enable_wal=False

# Test log rotation only
# Edit config.yaml, set max_bytes=1024 (1KB) to trigger rotation quickly
```

### Rolling Back Changes

All changes are backward compatible. To roll back:

1. **Remove new config sections** (system will use defaults)
2. **Disable WAL mode**:

   ```bash
   sqlite3 data/readings.db "PRAGMA journal_mode=DELETE;"
   ```

3. **Remove health check script** (optional, doesn't affect collection)

**No code changes required** - Sprint 1.0 code continues to work.

---

## Resources

- **Research Documentation**: [research.md](./research.md)
- **Data Model**: [data-model.md](./data-model.md)
- **Implementation Plan**: [plan.md](./plan.md)
- **SQLite WAL Mode**: https://www.sqlite.org/wal.html
- **Python RotatingFileHandler**: https://docs.python.org/3/library/logging.handlers.html

---

**Ready to implement?** Proceed to [tasks.md](./tasks.md) for step-by-step implementation tasks (generated separately with `/speckit.tasks` command).
