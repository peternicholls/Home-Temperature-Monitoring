# Manual Test: Log Rotation

**Feature**: US3 - Controlled Log File Growth  
**Objective**: Verify that log files automatically rotate at 10MB and maintain max 5 backups (60MB total)

## Prerequisites

- Log rotation configured in config.yaml
- RotatingFileHandler implemented in source/utils/logging.py
- Logging enabled for file output

## Test Procedure

### Test 1: Verify Log Rotation Configuration

1. **Check config.yaml** has rotation settings:
   ```bash
   grep -A 5 "^logging:" config/config.yaml
   ```

2. **Expected output**:
   ```yaml
   logging:
     level: "INFO"
     enable_file_logging: true
     log_file_path: "logs/hue_collection.log"
     max_bytes: 10485760  # 10MB
     backup_count: 5
     encoding: "utf-8"
   ```

### Test 2: Trigger Log Rotation (Quick Test)

For quick testing, temporarily reduce max_bytes to trigger rotation faster.

1. **Backup current config**:
   ```bash
   cp config/config.yaml config/config.yaml.backup
   ```

2. **Edit config.yaml** - change `max_bytes` to small value:
   ```yaml
   logging:
     max_bytes: 10240  # 10KB for testing
   ```

3. **Run continuous collection**:
   ```bash
   python source/collectors/hue_collector.py --continuous
   ```

4. **Monitor log directory** in separate terminal:
   ```bash
   watch -n 1 'ls -lh logs/'
   ```

5. **Expected behavior**:
   - `hue_collection.log` grows to ~10KB
   - Rotation creates `hue_collection.log.1`
   - Original `hue_collection.log` starts fresh
   - Process continues: `.log.2`, `.log.3`, etc.

6. **Stop collection** after 3-4 rotations (Ctrl+C)

7. **Verify rotation**:
   ```bash
   ls -lh logs/
   # Should show:
   # hue_collection.log (newest)
   # hue_collection.log.1
   # hue_collection.log.2
   # hue_collection.log.3
   ```

8. **Restore config**:
   ```bash
   mv config/config.yaml.backup config/config.yaml
   ```

### Test 3: Verify Backup Count Limit

1. **Edit config** to set small max_bytes and low backup_count:
   ```yaml
   logging:
     max_bytes: 5120  # 5KB
     backup_count: 2  # Only keep 2 backups
   ```

2. **Run collection** until 5+ rotations occur

3. **Check backup files**:
   ```bash
   ls -1 logs/hue_collection.log*
   ```

4. **Expected output** (max 3 files total):
   ```
   hue_collection.log
   hue_collection.log.1
   hue_collection.log.2
   ```

5. **Verify oldest deleted**: No `.log.3`, `.log.4`, etc. files present

6. **Restore config**:
   ```bash
   git checkout config/config.yaml
   ```

### Test 4: Long-Running Log Accumulation (Production Test)

This test runs in production mode (10MB limit, 5 backups).

1. **Ensure production config**:
   ```yaml
   logging:
     max_bytes: 10485760  # 10MB
     backup_count: 5
   ```

2. **Calculate total allowed disk usage**:
   - Active log: 10MB
   - Backups: 5 × 10MB = 50MB
   - **Total max: 60MB**

3. **Run continuous collection** for extended period:
   ```bash
   # Run in background
   nohup python source/collectors/hue_collector.py --continuous > /dev/null 2>&1 &
   echo $! > collection.pid
   ```

4. **Monitor disk usage** periodically:
   ```bash
   du -sh logs/
   # Should never exceed 60MB
   ```

5. **Check after 24 hours**:
   ```bash
   du -sh logs/
   ls -lh logs/
   ```

6. **Expected results**:
   - Total size ≤ 60MB
   - Max 6 files (1 active + 5 backups)
   - Oldest logs automatically deleted

7. **Stop collection**:
   ```bash
   kill $(cat collection.pid)
   rm collection.pid
   ```

### Test 5: Log Content Integrity

Verify that rotation doesn't corrupt or lose log entries.

1. **Run collection** with small rotation (10KB limit)

2. **Count total log entries**:
   ```bash
   cat logs/hue_collection.log* | wc -l
   ```

3. **Check for split entries** (entries cut mid-line):
   ```bash
   # Check end of rotated file
   tail -n 3 logs/hue_collection.log.1
   
   # Check start of next file
   head -n 3 logs/hue_collection.log
   ```

4. **Expected**: No partial log entries, clean rotation at message boundaries

### Test 6: File Permissions

1. **Check log file permissions**:
   ```bash
   ls -la logs/
   ```

2. **Expected permissions**:
   - Files: `-rw-r--r--` (644)
   - Directory: `drwxr-xr-x` (755)

3. **Verify encoding**:
   ```bash
   file logs/hue_collection.log
   # Should show: UTF-8 Unicode text
   ```

## Success Criteria

- ✅ **Rotation occurs at 10MB threshold** (or configured max_bytes)
- ✅ **Backup count enforced** (oldest files deleted when limit reached)
- ✅ **Total disk usage bounded** (≤ max_bytes × (1 + backup_count))
- ✅ **No log entry corruption** during rotation
- ✅ **Process continues uninterrupted** during rotation
- ✅ **Proper file encoding** (UTF-8)

## Measurements Table

| Metric | Expected | Actual | Pass/Fail |
|--------|----------|--------|-----------|
| Max file size | 10MB | - | - |
| Backup count | 5 files | - | - |
| Total disk usage | ≤60MB | - | - |
| Rotation integrity | No lost entries | - | - |
| File encoding | UTF-8 | - | - |

## Debugging

If rotation not working:

1. **Check handler type**:
   ```bash
   grep "RotatingFileHandler" source/utils/logging.py
   # Should be present
   ```

2. **Verify log directory exists**:
   ```bash
   ls -ld logs/
   # Should exist with write permissions
   ```

3. **Check for errors**:
   ```bash
   grep -i "error\|permission denied" logs/hue_collection.log
   ```

4. **Test manual rotation**:
   ```python
   from logging.handlers import RotatingFileHandler
   handler = RotatingFileHandler('test.log', maxBytes=1024, backupCount=2)
   for i in range(1000):
       handler.emit(logging.LogRecord('test', logging.INFO, '', 0, f'Test message {i}', (), None))
   ```

## Cleanup

After testing:

```bash
# Remove test logs if desired
rm -f logs/hue_collection.log*

# Or keep for production monitoring
```

## Related Documentation

- [Research: Log Rotation](../../specs/003-system-reliability/research.md#research-task-4-log-rotation---rotatingfilehandler-best-practices)
- [Data Model: Log Rotation Configuration](../../specs/003-system-reliability/data-model.md#entity-2-log-rotation-configuration)
