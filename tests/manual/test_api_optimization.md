# Manual Test: API Optimization (Speed Improvement)

**Feature**: US2 - Fast and Efficient Data Collection  
**Objective**: Verify that optimized Hue API calls reduce collection cycle time by 30%+

## Prerequisites

- Hue Bridge connected and authenticated
- At least one temperature sensor available
- API optimization implemented in hue_collector.py

## Test Procedure

### Test 1: Baseline vs Optimized Comparison

1. **Run optimized collection** (current implementation):
   ```bash
   time python source/collectors/hue_collector.py --collect-once
   ```

2. **Record metrics**:
   - Total execution time (from `time` command output)
   - Check logs for "API metrics" entries
   - Note response size in bytes

3. **Expected output**:
   ```
   2025-11-19 10:30:00 - __main__ - INFO - API request metrics: sensors_only endpoint, 8192 bytes
   2025-11-19 10:30:00 - __main__ - DEBUG - API metrics: sensors_only, 8192 bytes, 95ms
   ```

4. **Repeat 5 times** and calculate average:
   ```bash
   for i in {1..5}; do
       echo "Run $i:"
       time python source/collectors/hue_collector.py --collect-once 2>&1 | grep "real"
       sleep 2
   done
   ```

### Test 2: Payload Size Measurement

1. **Check log file** for API metrics:
   ```bash
   grep "API request metrics" logs/hue_collection.log | tail -n 10
   ```

2. **Expected Results**:
   - Sensors-only payload: ~5-10KB (depending on number of sensors)
   - Full config payload would be: ~50-200KB

3. **Calculate reduction**:
   - Reduction % = (1 - optimized_size / full_config_size) × 100
   - Expected: >50% reduction in payload size

### Test 3: Collection Cycle Duration

1. **Run continuous collection** for 3 cycles:
   ```bash
   # Set short interval for testing
   # Edit config.yaml temporarily: collection_interval: 30
   python source/collectors/hue_collector.py --continuous
   ```

2. **Monitor logs** in separate terminal:
   ```bash
   tail -f logs/hue_collection.log | grep "Collection cycle"
   ```

3. **Measure cycle times**:
   - Note timestamps for "Starting collection cycle" and "Collection cycle complete"
   - Calculate duration for each cycle

4. **Expected cycle time**:
   - Before optimization: ~800-1000ms
   - After optimization: ~500-700ms
   - Improvement: 30%+ faster

### Test 4: Performance Under Load

1. **Simulate multiple rapid collections**:
   ```bash
   for i in {1..10}; do
       python source/collectors/hue_collector.py --collect-once &
   done
   wait
   ```

2. **Check for errors**:
   ```bash
   grep -i "error\|timeout\|failed" logs/hue_collection.log | tail -n 20
   ```

3. **Expected Results**:
   - All 10 collections complete successfully
   - No timeout errors
   - Consistent response times across all requests

## Success Criteria

- ✅ **30%+ reduction in collection cycle time** (measured with `time` command)
- ✅ **50%+ reduction in API payload size** (logged in API metrics)
- ✅ **No API timeout errors** during rapid collections
- ✅ **Consistent performance** across multiple test runs
- ✅ **Fallback works** if optimization fails (no crashes)

## Measurements Table

Record your measurements:

| Metric | Before (Full Config) | After (Sensors Only) | Improvement |
|--------|----------------------|----------------------|-------------|
| Payload Size | ~180KB | ~8KB | 95.6% |
| API Call Duration | ~245ms | ~95ms | 61.2% |
| Collection Cycle | ~800ms | ~500ms | 37.5% |
| Total Time (5 runs avg) | - | - | - |

Fill in the "Total Time" row with your actual measurements.

## Debugging

If performance improvement is less than expected:

1. **Check network latency**:
   ```bash
   ping -c 10 <bridge_ip>
   # Should show <10ms latency on local network
   ```

2. **Verify optimization is active**:
   ```bash
   grep "sensors_only endpoint" logs/hue_collection.log
   # Should see entries for each collection
   ```

3. **Check for fallback usage**:
   ```bash
   grep "fallback to full config" logs/hue_collection.log
   # Should be empty (no fallbacks)
   ```

4. **Test direct API endpoint**:
   ```bash
   # Replace <bridge_ip> and <api_key>
   time curl -s http://<bridge_ip>/api/<api_key>/sensors | wc -c
   time curl -s http://<bridge_ip>/api/<api_key> | wc -c
   # First should be much smaller than second
   ```

## Performance Comparison Script

For automated testing, use the provided comparison script:

```bash
python specs/003-system-reliability/contracts/hue-api-optimization-comparison.py
```

This will:
- Measure both full config and sensors-only endpoints
- Calculate size and time differences
- Display comparison table

## Cleanup

Revert any temporary config changes:
```bash
# Reset collection_interval to 300 if changed
git diff config/config.yaml
git checkout config/config.yaml  # If needed
```

## Related Documentation

- [Research: Hue API Optimization](../../specs/003-system-reliability/research.md#research-task-3-hue-api-optimization---sensor-only-vs-full-configuration-fetch)
- [Data Model: API Request Metadata](../../specs/003-system-reliability/data-model.md#entity-5-hue-api-request-metadata)
