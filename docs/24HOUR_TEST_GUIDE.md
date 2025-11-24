# Production Testing - 24 Hour Continuous Operation Test Guide

**Sprint**: 005-system-reliability  
**Phase**: 8 (Integration Testing & Validation)  
**Tasks**: T101-T104

This guide walks you through running the 24-hour continuous operation test using the `make` commands.

---

## Overview

The 24-hour test validates:
- **T101**: Concurrent collector operation for extended periods
- **T102**: SC-001 (100% zero data loss)
- **T103**: SC-002 (95%+ retry success rate for transient failures)
- **T104**: SC-008 (7-day unattended operation capability)

---

## Quick Start

### 1. Setup Test Environment

```bash
# Verify configuration is in place
ls config/config.yaml config/secrets.yaml

# Create clean database (optional, backup existing first)
make db-reset

# Verify system is healthy
make health-check
```

### 2. Start 24-Hour Test

```bash
# Launch both collectors in background
make test-24hour-setup
```

Output shows:
- Hue collector PID
- Amazon AQM collector PID
- Log file locations
- Test start time

### 3. Monitor Progress (While Test Runs)

```bash
# View recent readings
make db-view

# Check database statistics
make db-stats

# Follow logs in real-time
tail -f logs/hue_24h_test.log
tail -f logs/amazon_24h_test.log

# Custom queries
make db-query SQL="SELECT COUNT(*) FROM readings WHERE device_type='hue'"
```

### 4. Stop Test After 24 Hours

```bash
make test-24hour-stop
```

This gracefully stops both collectors and preserves test metadata.

### 5. Verify Results

```bash
make test-24hour-verify
```

This generates a comprehensive report showing:
- ✓ **T102**: Data loss verification (should be zero)
- ✓ **T103**: Retry success rate (should be ≥95%)
- ✓ **T112**: Database lock errors (should be zero)
- ✓ **T104**: Resource usage (disk, memory)

---

## Detailed Workflow

### Before Starting

**Pre-Test Checklist**:
1. ✓ Virtual environment activated: `source venv/bin/activate`
2. ✓ Configuration valid: `config/config.yaml` and `config/secrets.yaml` present
3. ✓ Hue Bridge credentials working: `make discover` returns devices
4. ✓ Amazon AQM credentials working: `make aqm-discover` returns devices
5. ✓ Network stable (not WiFi-only, prefer ethernet if possible)
6. ✓ Disk space available: `df -h` shows >5GB free
7. ✓ Fresh database or backup existing: `make db-stats` to verify current state

### Running the Test

**T101: Setup & Start** (5 minutes)

```bash
make test-24hour-setup
```

This:
1. Verifies configuration files exist
2. Creates baseline snapshot (reading count, DB size)
3. Starts Hue collector in background
4. Starts Amazon AQM collector in background
5. Records PIDs and test metadata in `/tmp/test_24h_info.txt`

**Expected Output**:
```
✓ Test started successfully!

Monitor Progress:
  • Check logs: tail -f logs/hue_24h_test.log
  • Check logs: tail -f logs/amazon_24h_test.log
  • Database: make db-view
  • Stats: make db-stats

Stop Test:
  make test-24hour-stop

Verify Results After 24 Hours:
  make test-24hour-verify
```

**Monitoring During Test** (24 hours)

Check every 2-4 hours:

```bash
# View recent readings
make db-view

# Check for errors
grep -i "error\|critical" logs/hue_24h_test.log | tail -20
grep -i "error\|critical" logs/amazon_24h_test.log | tail -20

# Check for database locks (should be none)
grep "database.*locked" logs/*.log
```

**Abort Test If**:
- Database lock errors appear: ❌ WAL mode not working
- Memory usage growing continuously: ❌ Memory leak
- Unrecoverable errors in logs: ❌ System unstable

**T101: Stop** (1 minute)

After 24 hours, gracefully stop the test:

```bash
make test-24hour-stop
```

This:
1. Kills Hue collector gracefully
2. Kills Amazon AQM collector gracefully
3. Cleans up PIDs file
4. Preserves test info for verification

### Verification

**T102-T104: Verify Results** (5 minutes)

```bash
make test-24hour-verify
```

Generates detailed report with:

```
T102: SC-001 Verification (100% readings stored, zero data loss)
  Initial readings: X
  Final readings: Y
  New readings: Z
  Expected minimum: W
  Status: ✓ PASS or ✗ FAIL

T103: SC-002 Verification (95%+ retry success rate)
  Hue: XX successful, Y failed = ZZ%
  Amazon: AA successful, B failed = CC%
  Combined: DD% (target: 95%+)
  Status: ✓ PASS or ✗ FAIL

T112: SC-007 Verification (Retry consistency, comprehensive logging)
  Database lock errors: 0 (target: 0)
  Error/critical events: X
  Status: ✓ PASS or ✗ FAIL

Summary:
  ✓ All verifications PASSED - System ready for production
```

---

## Success Criteria

### T102: SC-001 (Zero Data Loss) ✓

- New readings ≥ (expected minimum based on test duration)
- Expected: ~120 readings/hour (60 per collector)
- For 24-hour test: minimum 2,880 readings
- No gaps >30 minutes in time slots

### T103: SC-002 (95%+ Retry Success) ✓

- Retry success rate ≥ 95%
- Calculated: successful_retries / (successful_retries + failed_retries)
- Both collectors should show >95% individually

### T112: SC-007 (Retry Consistency) ✓

- Zero "database locked" errors in logs
- Consistent retry patterns between collectors
- Comprehensive retry logging present

### T104: Resource Usage ✓

- Database size: <1GB (well within bounds)
- Log files total: <100MB
- Memory usage: stable, no continuous growth

---

## Troubleshooting

### "Database is locked" Errors

**Problem**: T112 verification shows database lock errors  
**Cause**: WAL mode not enabled or concurrency issue  
**Solution**:
```bash
# Check WAL mode
sqlite3 data/temperature.db "PRAGMA journal_mode;"  # Should return "wal"

# Verify WAL files
ls -la data/temperature.db*

# Run health check
make health-check
```

### Low Retry Success Rate (<95%)

**Problem**: T103 shows <95% success rate  
**Cause**: Network issues or API problems  
**Solution**:
```bash
# Check logs for specific errors
grep "retry.*failed\|max attempts" logs/hue_24h_test.log
grep "retry.*failed\|max attempts" logs/amazon_24h_test.log

# Verify credentials
make discover
make aqm-discover

# Check network
ping -c 5 8.8.8.8  # Test internet connectivity
```

### Test Crashes Before 24 Hours

**Problem**: Collectors stop running before 24 hours  
**Cause**: Crash, memory exhaustion, or crash loop  
**Solution**:
```bash
# Check if processes still running
ps aux | grep collector

# View end of logs
tail -100 logs/hue_24h_test.log
tail -100 logs/amazon_24h_test.log

# Check system resources
top -b -n 1 | head -20  # Memory/CPU usage

# Restart test
make test-24hour-stop
make db-reset  # If needed
make test-24hour-setup
```

### Data Gap Issues

**Problem**: T102 verification shows significant gaps  
**Cause**: Collector crashes, long retries, API unavailability  
**Solution**:
```bash
# Check for gaps in the data
sqlite3 data/temperature.db << EOF
SELECT strftime('%Y-%m-%d %H:%M', timestamp) as time_slot, COUNT(*) as count
FROM readings
GROUP BY time_slot
HAVING COUNT(*) < 2
ORDER BY time_slot DESC
LIMIT 10;
EOF

# Check logs for that time period
grep "2025-11-22 14:30" logs/hue_24h_test.log
```

---

## Extended Testing: 7-Day Test (T104)

For T104 (SC-008: 7-day unattended operation):

```bash
# Same as 24-hour, but run for 7 days
make test-24hour-setup

# Monitor same way as 24-hour test
make db-view  # Check periodically
make db-stats

# After 7 days
make test-24hour-stop
make test-24hour-verify
```

Verify same success criteria, plus:
- System requires zero manual intervention
- Log rotation working correctly (files not filling disk)
- No memory leaks over 7 days

---

## Files & Logs

**Test Scripts**:
- `scripts/test-24hour-setup.sh` - T101: Start test
- `scripts/test-24hour-stop.sh` - Stop test
- `scripts/test-24hour-verify.sh` - T102-T104: Verify results

**Test Data**:
- `/tmp/test_24h_info.txt` - Test metadata (start time, PIDs, initial counts)
- `/tmp/test_24h_pids.txt` - Process IDs for stopping

**Log Files**:
- `logs/hue_24h_test.log` - Hue collector 24-hour test logs
- `logs/amazon_24h_test.log` - Amazon AQM 24-hour test logs
- `logs/hue_collection.log` - Normal Hue logs (if overwritten)
- `logs/amazon_aqm.log` - Normal Amazon logs (if overwritten)

---

## Next Steps After Success

Once all 24-hour test verifications pass (T102-T104):

1. **Document Results**: Create test report with final numbers
2. **Proceed to Phase 9**: User Story 6 (Device Registry)
   ```bash
   # Start Phase 9 tasks
   make test-device-registry-setup  # When available
   ```
3. **Optional: 7-Day Test**: Run extended T104 validation if needed
4. **Production Deployment**: System is production-ready

---

## Quick Reference

```bash
# Start test
make test-24hour-setup

# Monitor
make db-view
make db-stats
tail -f logs/hue_24h_test.log

# Stop test
make test-24hour-stop

# Verify
make test-24hour-verify
```

---

**Last Updated**: 21 November 2025  
**Sprint**: 005-system-reliability  
**Phase**: 8 (Integration Testing & Validation)
