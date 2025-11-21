# Contracts: Structured JSON Logging

**Specification:** Spec 007 - Structured Log Formatting  
**Date:** 2025-11-21

## Test Contract 1: Log Format Validation

### Requirement
All log lines must be valid JSON with required fields.

### Test Cases

#### T701: Hue Collector Emits Valid JSON
```bash
# When: Hue collector runs
# Then: Every log line is valid JSON
# And: Every entry has: timestamp, level, component, message

python -m source.collectors.hue_collector --collect-once 2>&1 | \
  while IFS= read -r line; do
    python3 -m json.tool <<< "$line" > /dev/null 2>&1 || echo "INVALID: $line"
  done
# Expected: No INVALID lines
```

#### T702: Amazon Collector Emits Valid JSON
```bash
# Same as T701 but for Amazon collector
```

#### T703: All Required Fields Present
```bash
# Validate: timestamp, level, component, message in every line
python -m source.collectors.hue_collector --collect-once 2>&1 | \
  jq -e '.timestamp and .level and .component and .message' \
    > /dev/null || echo "MISSING FIELD"
```

## Test Contract 2: Log Parsing

### Requirement
Log parser must correctly filter and aggregate logs.

### Test Cases

#### T704: Filter by Level
```bash
# When: Filtering logs by level
# Then: Only entries with matching level returned

make log-json | jq '.[] | select(.level=="ERROR")'
# Expected: Only ERROR entries returned
```

#### T705: Filter by Component
```bash
# When: Filtering logs by component
# Then: Only entries from specified component returned

make log-json | jq '.[] | select(.component=="hue_collector")'
# Expected: Only hue_collector entries
```

#### T706: Filter by Time Range
```bash
# When: Filtering logs by timestamp range
# Then: Only entries within range returned

start="2025-11-21T06:15:00Z"
end="2025-11-21T06:16:00Z"
make log-json | jq ".[] | select(.timestamp >= \"$start\" and .timestamp < \"$end\")"
# Expected: Only entries in 1-minute window
```

#### T707: Aggregate Statistics
```bash
# When: Running make log-stats
# Then: Statistics calculated correctly

make log-stats | grep "Success rate"
# Expected: Percentage calculated correctly
```

#### T708: Error Analysis
```bash
# When: Running make log-errors
# Then: All errors listed with details

make log-errors
# Expected: Error count matches actual errors in logs
```

## Test Contract 3: Console Integration

### Requirement
Logs must be viewable and parseable in Console.app.

### Test Cases

#### T709: Console.app Can Open Log File
```bash
open -a Console logs/hue_scheduled.log
# Expected: Logs display correctly in Console.app
# And: Each line is parsed as separate entry
```

#### T710: Console.app Search Works
```bash
# In Console.app:
# Search: "ERROR"
# Expected: All ERROR level entries appear
```

#### T711: JSON Syntax Highlighting
```bash
# In Console.app:
# Expected: JSON syntax is properly formatted
# (requires matching file extension: .json or tools that recognize JSON)
```

## Test Contract 4: 24-Hour Test Reporting

### Requirement
Logs from 24-hour test can be analyzed to generate pass/fail report.

### Test Cases

#### T712: Test Report Generation
```bash
make log-stats > test_report.txt
grep -E "Success rate|Average cycle|Error count" test_report.txt
# Expected: All key metrics present
```

#### T713: Error Rate Calculation
```bash
# After 24-hour test:
total=$(make log-json | jq '[.[] | select(.level=="ERROR")] | length')
cycles=$(make log-json | jq '[.[] | select(.component=="runner_script")] | length')
error_rate=$((total * 100 / cycles))
# Expected: error_rate <= 2% for success (configurable)
```

#### T714: Data Loss Detection
```bash
# Check if all expected collection cycles occurred
expected_cycles=$((24 * 60 / 5))  # 288 cycles in 24 hours
actual_cycles=$(make log-json | jq '[.[] | select(.message | contains("Collection cycle complete"))] | length')
# Expected: actual_cycles >= expected_cycles * 0.98 (98% success rate)
```

#### T715: Retry Success Rate
```bash
# Calculate retry success percentage
successful_retries=$(make log-json | jq '[.[] | select(.level=="INFO" and .message | contains("retry"))] | length')
failed_retries=$(make log-json | jq '[.[] | select(.level=="ERROR" and .message | contains("retry"))] | length')
retry_success_rate=$((successful_retries * 100 / (successful_retries + failed_retries)))
# Expected: retry_success_rate >= 95%
```

## Test Contract 5: Log Parser Performance

### Requirement
Log parser must process large log files quickly.

### Test Cases

#### T716: Parse 24h Logs in <1 second
```bash
# Given: logs/hue_scheduled.log with 288 entries (24h of 5-min cycles)
# When: Running make log-stats
# Then: Completes in <1 second

time make log-stats > /dev/null
# Expected: real time < 1.0s
```

#### T717: Filter 10K Entries Quickly
```bash
# Given: Large log file with 10,000 entries
# When: Filtering by component
# Then: Returns in <200ms

time make log-json | jq '.[] | select(.component=="hue_collector")' > /dev/null
# Expected: real time < 0.2s
```

## Expected Log Frequency (24-Hour Test)

- **Collection Cycles**: 288 (every 5 minutes)
- **Logs per Cycle**: 6-8 entries (start, connect, discover, collect, store, end)
- **Total Logs**: ~2,000 entries
- **Error Logs**: 0-5% (0-100 error entries)
- **Warning Logs**: 1-10% (20-200 warning entries)

## Success Criteria

✓ All log lines are valid JSON  
✓ Parser filters correctly by all fields  
✓ Statistics calculated accurately  
✓ Console.app displays logs properly  
✓ 24h test report generated automatically  
✓ Performance <1s for full log parsing  
✓ Error rate detectable and reportable  

## Files to Create/Modify

**Create:**
- `specs/007-log-formatting/spec.md`
- `specs/007-log-formatting/contracts.md`
- `source/utils/structured_logger.py`
- `source/utils/log_parser.py`

**Modify:**
- `source/collectors/hue_collector.py`
- `source/collectors/amazon_aqm_collector_main.py`
- `scripts/collectors-hue-runner.sh`
- `scripts/collectors-amazon-runner.sh`
- `Makefile`

## References

- Spec 007: `specs/007-log-formatting/spec.md`
- JSON Schema: https://json-schema.org/
- jq documentation: https://stedolan.github.io/jq/
