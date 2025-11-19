# Manual Test: Concurrent Collection (Database Reliability)

**Feature**: US1 - Reliable Data Collection Under Load  
**Objective**: Verify that multiple collection processes can run simultaneously without database locked errors

## Prerequisites

- WAL mode enabled in config.yaml
- Database retry logic implemented in DatabaseManager
- At least one Hue temperature sensor available

## Test Procedure

### Test 1: Concurrent Single Collections

1. **Open two terminal windows** in the project root

2. **Terminal 1**: Start first collection
   ```bash
   source venv/bin/activate
   python source/collectors/hue_collector.py --collect-once
   ```

3. **Terminal 2**: Start second collection immediately (within 1-2 seconds)
   ```bash
   source venv/bin/activate
   python source/collectors/hue_collector.py --collect-once
   ```

4. **Expected Results**:
   - Both processes complete successfully
   - No "database is locked" errors in logs
   - Both collections store readings (or detect duplicates)
   - Exit code 0 for both processes

5. **Check Logs**:
   ```bash
   tail -n 50 logs/hue_collection.log | grep -i "locked\|retry\|wal"
   ```
   
   Expected output:
   - "WAL mode enabled for database" (on first run)
   - No "database is locked" warnings
   - Possible "Duplicate reading detected" messages (if timestamps match)

### Test 2: Concurrent Continuous Collections

1. **Terminal 1**: Start continuous collection
   ```bash
   python source/collectors/hue_collector.py --continuous
   ```

2. **Terminal 2**: Start second continuous collection after 30 seconds
   ```bash
   python source/collectors/hue_collector.py --continuous
   ```

3. **Let both run for 5-10 minutes** (2-4 collection cycles each)

4. **Expected Results**:
   - Both processes continue running without crashes
   - No database locked errors
   - Each process collects and stores readings successfully
   - Duplicate detection works correctly (same timestamp readings)

5. **Stop both processes**: Press Ctrl+C in each terminal

6. **Verify database integrity**:
   ```bash
   sqlite3 data/readings.db "PRAGMA integrity_check;"
   # Should output: ok
   
   sqlite3 data/readings.db "PRAGMA journal_mode;"
   # Should output: wal
   
   sqlite3 data/readings.db "SELECT COUNT(*) FROM readings;"
   # Should show accumulated readings
   ```

### Test 3: Stress Test - Multiple Concurrent Processes

1. **Create a test script** `test_concurrent_stress.sh`:
   ```bash
   #!/bin/bash
   for i in {1..5}; do
       python source/collectors/hue_collector.py --collect-once &
   done
   wait
   echo "All processes completed"
   ```

2. **Run the stress test**:
   ```bash
   chmod +x test_concurrent_stress.sh
   ./test_concurrent_stress.sh
   ```

3. **Expected Results**:
   - All 5 processes complete successfully
   - No database errors
   - Exit message: "All processes completed"

4. **Check for errors**:
   ```bash
   grep -i "error\|failed\|locked" logs/hue_collection.log | tail -n 20
   ```
   
   Expected: No critical errors (duplicates are OK)

## Success Criteria

- ✅ **Zero database locked errors** during concurrent operations
- ✅ **100% process success rate** (all processes complete without crashes)
- ✅ **Data integrity maintained** (no corrupted readings)
- ✅ **WAL mode active** (verified via PRAGMA journal_mode)
- ✅ **Duplicate detection works** (same timestamp readings handled gracefully)

## Failure Scenarios

If test fails, check:

1. **WAL mode enabled?**
   ```bash
   sqlite3 data/readings.db "PRAGMA journal_mode;"
   ```
   If output is not "wal", check config.yaml `enable_wal_mode` setting

2. **Retry logic active?**
   - Check logs for "retrying in Xs..." messages
   - Verify `retry_max_attempts` in config.yaml

3. **Timeout settings?**
   - Check `busy_timeout_ms` in config.yaml
   - Increase if processes timeout too quickly

4. **File permissions?**
   ```bash
   ls -la data/
   # Ensure .db, .db-wal, .db-shm files are writable
   ```

## Performance Notes

**Before Sprint 1.1** (without WAL mode):
- Concurrent collections frequently fail with "database is locked"
- Retry logic needed 2-3 attempts per collision
- Success rate: ~70% on concurrent runs

**After Sprint 1.1** (with WAL mode):
- Concurrent collections succeed consistently
- Retries rare (only during checkpoint operations)
- Success rate: ~100% on concurrent runs

## Cleanup

After testing:
```bash
# Remove test script if created
rm -f test_concurrent_stress.sh

# Optional: Clear test data
# rm data/readings.db*
```

## Related Documentation

- [Research: SQLite WAL Mode](../../specs/003-system-reliability/research.md#research-task-1-sqlite-concurrency---wal-mode-vs-default-journal)
- [Data Model: Database Retry State](../../specs/003-system-reliability/data-model.md#entity-4-database-retry-state)
