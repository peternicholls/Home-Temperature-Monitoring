# Manual Test: Health Check

**Feature**: US4 - Pre-Collection System Validation  
**Objective**: Verify that health check validates all system components before collection

## Prerequisites

- Health check script created at source/verify_setup.py
- All system components configured (config, secrets, database, Hue Bridge)

## Test Procedure

### Test 1: Healthy System (All Checks Pass)

1. **Ensure system is properly configured**:
   ```bash
   ls config/config.yaml config/secrets.yaml data/readings.db
   # All files should exist
   ```

2. **Run health check**:
   ```bash
   python source/verify_setup.py
   ```

3. **Expected output**:
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
      Connected to bridge 192.168.1.xxx, 2 temperature sensor(s) discovered

   ============================================================
   📊 OVERALL STATUS: HEALTHY
   All 4 checks passed in 0.8s
   ============================================================
   ```

4. **Check exit code**:
   ```bash
   echo $?
   # Should output: 0 (success)
   ```

### Test 2: Missing Configuration File

1. **Temporarily rename config**:
   ```bash
   mv config/config.yaml config/config.yaml.backup
   ```

2. **Run health check**:
   ```bash
   python source/verify_setup.py
   ```

3. **Expected output**:
   ```
   ❌ Configuration: FAIL
      Config file not found: config/config.yaml
   ```

4. **Check exit code**:
   ```bash
   echo $?
   # Should output: 1 (failure)
   ```

5. **Restore config**:
   ```bash
   mv config/config.yaml.backup config/config.yaml
   ```

### Test 3: Missing Secrets File

1. **Temporarily rename secrets**:
   ```bash
   mv config/secrets.yaml config/secrets.yaml.backup
   ```

2. **Run health check**:
   ```bash
   python source/verify_setup.py
   ```

3. **Expected output**:
   ```
   ❌ Secrets: FAIL
      Secrets file not found: config/secrets.yaml. Run: python source/collectors/hue_auth.py
   ```

4. **Restore secrets**:
   ```bash
   mv config/secrets.yaml.backup config/secrets.yaml
   ```

### Test 4: Database Write Error

1. **Make database read-only**:
   ```bash
   chmod 444 data/readings.db
   ```

2. **Run health check**:
   ```bash
   python source/verify_setup.py
   ```

3. **Expected output**:
   ```
   ❌ Database: FAIL
      Database error: attempt to write a readonly database
   ```

4. **Restore write permissions**:
   ```bash
   chmod 644 data/readings.db
   ```

### Test 5: Hue Bridge Unreachable

1. **Edit config** to use invalid bridge IP:
   ```bash
   # Backup config
   cp config/config.yaml config/config.yaml.backup
   
   # Edit to set invalid IP
   sed -i.bak 's/bridge_ip: null/bridge_ip: "192.168.1.999"/' config/config.yaml
   ```

2. **Run health check**:
   ```bash
   python source/verify_setup.py
   ```

3. **Expected output**:
   ```
   ❌ Hue Bridge: FAIL
      Bridge connection failed: <error details>
   ```

4. **Restore config**:
   ```bash
   mv config/config.yaml.backup config/config.yaml
   ```

### Test 6: Integration with Collection Workflow

1. **Use health check as pre-condition**:
   ```bash
   python source/verify_setup.py && python source/collectors/hue_collector.py --collect-once
   ```

2. **Expected behavior**:
   - Health check runs first
   - If PASS: Collection proceeds
   - If FAIL: Collection never starts

3. **Test failure case**:
   ```bash
   # Make system unhealthy
   mv config/secrets.yaml config/secrets.yaml.backup
   
   # Run combined command
   python source/verify_setup.py && python source/collectors/hue_collector.py --collect-once
   # Should stop after health check fails
   
   # Restore
   mv config/secrets.yaml.backup config/secrets.yaml
   ```

### Test 7: WAL Mode Detection

1. **Run health check** on fresh database:
   ```bash
   rm data/readings.db*
   python source/verify_setup.py
   ```

2. **Expected output**:
   ```
   ✅ Database: PASS
      Database write test successful (WAL mode NOT enabled (will be enabled on first collection))
   ```

3. **Run collection once** to enable WAL:
   ```bash
   python source/collectors/hue_collector.py --collect-once
   ```

4. **Run health check again**:
   ```bash
   python source/verify_setup.py
   ```

5. **Expected output**:
   ```
   ✅ Database: PASS
      Database write test successful (WAL mode enabled)
   ```

### Test 8: Performance Timing

1. **Measure health check duration**:
   ```bash
   time python source/verify_setup.py
   ```

2. **Expected timing**:
   - Total time: <10 seconds
   - Configuration check: <0.1s
   - Secrets check: <0.1s
   - Database check: <0.5s
   - Hue Bridge check: <2s (network dependent)

3. **Multiple runs** should have consistent timing:
   ```bash
   for i in {1..5}; do
       echo "Run $i:"
       time python source/verify_setup.py 2>&1 | grep "real"
   done
   ```

### Test 9: Automation Integration (Cron)

1. **Create test cron job** (don't install yet):
   ```bash
   cat > test_cron_entry.txt << 'EOF'
   # Health check before each collection
   */5 * * * * cd /path/to/HomeTemperatureMonitoring && python source/verify_setup.py && python source/collectors/hue_collector.py --collect-once >> logs/cron.log 2>&1
   EOF
   ```

2. **Test manually** with full path:
   ```bash
   cd /Users/peternicholls/Dev/HomeTemperatureMonitoring && python source/verify_setup.py && python source/collectors/hue_collector.py --collect-once
   ```

3. **Expected**: Both commands execute in sequence, collection only if healthy

## Success Criteria

- ✅ **All checks execute** in sequence
- ✅ **Exit code 0** when all checks pass
- ✅ **Exit code 1** when any check fails
- ✅ **Helpful error messages** for each failure type
- ✅ **Execution time <10 seconds** (network dependent)
- ✅ **WAL mode detected** correctly
- ✅ **Integration with collection** works (&&operator)

## Test Results Table

| Test Case | Component | Expected Exit Code | Actual Exit Code | Pass/Fail |
|-----------|-----------|--------------------|--------------------|-----------|
| Healthy system | All | 0 | - | - |
| Missing config | Configuration | 1 | - | - |
| Missing secrets | Secrets | 1 | - | - |
| Database read-only | Database | 1 | - | - |
| Bridge unreachable | Hue Bridge | 1 | - | - |
| Integration test | All | 0 (if healthy) | - | - |

## Debugging

If health check fails unexpectedly:

1. **Check Python version**:
   ```bash
   python --version
   # Should be 3.11+
   ```

2. **Check dependencies**:
   ```bash
   pip list | grep -E "phue|PyYAML"
   # Both should be installed
   ```

3. **Run with debug logging**:
   ```bash
   python -u source/verify_setup.py
   ```

4. **Check individual components**:
   ```bash
   # Test config loading
   python -c "import yaml; print(yaml.safe_load(open('config/config.yaml')))"
   
   # Test database access
   sqlite3 data/readings.db "SELECT 1;"
   
   # Test bridge connectivity
   ping -c 3 <bridge_ip>
   ```

## Cleanup

After testing:

```bash
# Remove test files
rm -f test_cron_entry.txt config/*.backup

# Ensure permissions are correct
chmod 644 config/config.yaml config/secrets.yaml
chmod 644 data/readings.db
```

## Production Usage

Add to workflow scripts:

```bash
# Collection script with health check
#!/bin/bash
set -e  # Exit on error

cd /path/to/HomeTemperatureMonitoring
source venv/bin/activate

# Pre-flight check
python source/verify_setup.py || {
    echo "Health check failed, aborting collection"
    exit 1
}

# Collection
python source/collectors/hue_collector.py --collect-once
```

## Related Documentation

- [Research: Health Check Design](../../specs/003-system-reliability/research.md#research-task-5-health-check-design---command-structure-and-validation-scope)
- [Data Model: Health Check Result](../../specs/003-system-reliability/data-model.md#entity-3-health-check-result)
- [Quickstart: Verify Setup](../../specs/003-system-reliability/quickstart.md#step-2-verify-setup)
