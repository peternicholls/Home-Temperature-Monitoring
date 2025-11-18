# Quickstart: Philips Hue Temperature Collection

**Feature**: 002-hue-integration  
**Date**: 2025-11-18  
**Status**: Implementation Complete ✅

## Overview

This quickstart guide walks you through setting up Philips Hue temperature collection, from authenticating with your Hue Bridge to running automated data collection.

**Time to Complete**: 15-20 minutes  
**Prerequisites**: Philips Hue Bridge on local network, at least one Hue motion sensor with temperature capability

---

## Step 1: Install Dependencies

```bash
cd /Users/peternicholls/Dev/HomeTemperatureMonitoring

# Install required Python packages
pip install phue==1.1

# Or update requirements.txt and install all
echo "phue==1.1" >> requirements.txt
pip install -r requirements.txt
```

**Expected Output**:
```
Successfully installed phue-1.1 requests-2.31.0
```

---

## Step 2: Configure Secrets

```bash
# Copy the secrets template
cp specs/002-hue-integration/contracts/secrets-hue.yaml.example config/secrets.yaml

# Edit secrets.yaml (will be populated during authentication)
# For now, leave placeholder values - authentication script will update them
```

**File Location**: `config/secrets.yaml`  
**Note**: This file is gitignored - never commit it

---

## Step 3: Update Configuration

Add Hue settings to your main `config/config.yaml`:

```bash
# Copy Hue configuration template
cat specs/002-hue-integration/contracts/config-hue.yaml >> config/config.yaml
```

**Or manually add**:

```yaml
hue:
  bridge_ip: null              # Auto-discovery enabled
  auto_discover: true
  collection_interval: 300     # 5 minutes
  retry_attempts: 3
  retry_backoff_base: 2
  
  sensor_locations:            # Optional: Map sensor IDs to rooms
    # "SENSOR_UNIQUE_ID": "Room Name"
  
  fallback_to_name: true
  temperature_min: 0.0
  temperature_max: 40.0
  collect_battery_level: true
  collect_signal_strength: true
  collect_raw_response: false
```

---

## Step 4: Authenticate with Hue Bridge

**This is a one-time setup step.**

```bash
# Run authentication script
python source/collectors/hue_auth.py
```

**What happens**:
1. Script discovers Hue Bridge on your network (or uses manual IP if configured)
2. Prompts you to press the physical button on the Hue Bridge
3. Generates API key and Bridge ID
4. Automatically updates `config/secrets.yaml` with credentials

**Expected Output**:
```
[INFO] Discovering Hue Bridge on network...
[INFO] Found Bridge at 192.168.1.100
[INFO] Press the button on your Hue Bridge now...
[INFO] Waiting for button press... (30 seconds)
[SUCCESS] Authentication successful!
[INFO] API Key: abc123def456...
[INFO] Bridge ID: 001788fffe100200
[INFO] Credentials saved to config/secrets.yaml
```

**Troubleshooting**:
- **"No Bridge found"**: Set `bridge_ip` manually in `config/config.yaml`
- **"Button not pressed"**: You have 30 seconds to press the button after prompt
- **"Authentication failed"**: Restart script and try again

---

## Step 5: Discover Sensors

Verify your Hue temperature sensors are detected:

```bash
# Run sensor discovery
python source/collectors/hue_collector.py --discover
```

**Expected Output**:
```
[INFO] Connected to Hue Bridge: 001788fffe100200
[INFO] Discovered 3 temperature sensors:

Sensor ID: 1
  Name: Hue temperature sensor 1
  Location: Living Room
  Unique ID: 00:17:88:01:02:03:04:05-02-0402
  Model: SML001
  Battery: 87%
  Reachable: Yes

Sensor ID: 2
  Name: Bedroom motion sensor
  Location: Bedroom
  Unique ID: 00:17:88:01:02:03:04:06-02-0402
  Model: SML001
  Battery: 62%
  Reachable: Yes

Sensor ID: 3
  Name: Kitchen sensor
  Location: Kitchen
  Unique ID: 00:17:88:01:02:03:04:07-02-0402
  Model: SML001
  Battery: 18%
  Reachable: No (offline)

[INFO] 2/3 sensors online and ready for collection
```

**Update Sensor Locations** (optional):

If you want custom room names, edit `config/config.yaml`:

```yaml
hue:
  sensor_locations:
    "00:17:88:01:02:03:04:05-02-0402": "Main Living Area"
    "00:17:88:01:02:03:04:06-02-0402": "Master Bedroom"
    "00:17:88:01:02:03:04:07-02-0402": "Kitchen & Dining"
```

---

## Step 6: Test Data Collection

Run a single collection cycle manually:

```bash
# Collect temperature data once
python source/collectors/hue_collector.py --collect-once
```

**Expected Output**:
```
[INFO] Starting Hue temperature collection...
[INFO] Connected to Bridge: 001788fffe100200
[INFO] Collecting from 2 reachable sensors...

[INFO] Sensor: Living Room
  Temperature: 21.34°C
  Battery: 87%
  Device ID: hue:00:17:88:01:02:03:04:05-02-0402
  Timestamp: 2025-11-18T14:30:00+00:00
  [✓] Stored in database

[INFO] Sensor: Bedroom
  Temperature: 19.87°C
  Battery: 62%
  Device ID: hue:00:17:88:01:02:03:04:06-02-0402
  Timestamp: 2025-11-18T14:30:05+00:00
  [✓] Stored in database

[WARNING] Sensor: Kitchen (offline - skipped)

[SUCCESS] Collection complete: 2/3 sensors successful
[INFO] Database: data/temperature.db
```

---

## Step 7: Verify Database Storage

Check that data was stored correctly:

```bash
# Query recent readings
sqlite3 data/temperature.db "
SELECT 
  datetime(timestamp) as time,
  location,
  temperature_celsius,
  battery_level,
  is_anomalous
FROM temperature_readings
WHERE device_type = 'hue_sensor'
ORDER BY timestamp DESC
LIMIT 5;
"
```

**Expected Output**:
```
2025-11-18 14:30:05|Bedroom|19.87|62|0
2025-11-18 14:30:00|Living Room|21.34|87|0
```

---

## Step 8: Enable Automated Collection

Set up scheduled collection every 5 minutes:

```bash
# Run collection in continuous mode
python source/collectors/hue_collector.py --continuous

# Or use launchd for macOS automation (see Sprint 3)
```

**Continuous Mode Output**:
```
[INFO] Starting continuous collection (interval: 300 seconds)
[INFO] Press Ctrl+C to stop

[INFO] Collection cycle 1 - 2025-11-18 14:30:00
[SUCCESS] 2/3 sensors collected

[INFO] Next collection in 5 minutes...

[INFO] Collection cycle 2 - 2025-11-18 14:35:00
[SUCCESS] 2/3 sensors collected
```

**Stop Collection**: Press `Ctrl+C`

---

## Step 9: Monitor Logs

Check collection logs for errors or anomalies:

```bash
# View recent log entries
tail -f logs/hue_collection.log
```

**Example Log Output**:
```
2025-11-18 14:30:00 - hue_collector - INFO - Collection cycle started
2025-11-18 14:30:01 - hue_collector - INFO - Connected to Bridge: 001788fffe100200
2025-11-18 14:30:02 - hue_collector - INFO - Discovered 3 sensors, 2 reachable
2025-11-18 14:30:03 - hue_collector - INFO - Collected: Living Room = 21.34°C
2025-11-18 14:30:04 - hue_collector - INFO - Collected: Bedroom = 19.87°C
2025-11-18 14:30:04 - hue_collector - WARNING - Sensor Kitchen offline, skipping
2025-11-18 14:30:05 - storage.manager - INFO - Inserted 2 readings into database
2025-11-18 14:30:05 - hue_collector - INFO - Collection cycle complete
```

---

## Step 10: Validate Data Quality

Run validation checks to ensure data integrity:

```bash
# Check for anomalous readings
sqlite3 data/temperature.db "
SELECT 
  COUNT(*) as total_readings,
  SUM(is_anomalous) as anomalous_count,
  ROUND(SUM(is_anomalous) * 100.0 / COUNT(*), 2) as anomaly_percent
FROM temperature_readings
WHERE device_type = 'hue_sensor';
"
```

**Expected Output** (healthy system):
```
total_readings|anomalous_count|anomaly_percent
150|0|0.0
```

```bash
# Check collection success rate (last 24 hours)
sqlite3 data/temperature.db "
SELECT 
  location,
  COUNT(*) as readings_count,
  ROUND(COUNT(*) * 100.0 / 288, 2) as success_rate_percent
FROM temperature_readings
WHERE device_type = 'hue_sensor'
  AND timestamp >= datetime('now', '-1 day')
GROUP BY location
ORDER BY success_rate_percent DESC;
"
```

**Expected Output** (5-minute intervals = 288/day):
```
location|readings_count|success_rate_percent
Living Room|285|99.0
Bedroom|282|97.9
Kitchen|120|41.7
```

---

## Troubleshooting

### Bridge Connection Issues

**Problem**: `Connection refused` or `Bridge not found`

**Solutions**:
1. Verify Bridge is on same network: `ping <bridge_ip>`
2. Check Bridge IP hasn't changed (DHCP): Re-run authentication
3. Set static IP in router or use manual `bridge_ip` in config
4. Restart Hue Bridge (unplug, wait 10s, plug back in)

### Authentication Failures

**Problem**: `Unauthorized` or `Invalid API key`

**Solutions**:
1. Delete `config/secrets.yaml` and re-authenticate
2. Check button was pressed within 30-second window
3. Ensure only one authentication attempt at a time
4. Verify Bridge firmware is up to date (Hue app)

### Missing Sensors

**Problem**: Fewer sensors than expected

**Solutions**:
1. Check sensor batteries (replace if <20%)
2. Verify sensors are paired to Bridge (Hue app)
3. Filter by type: Only `ZLLTemperature` sensors are collected
4. Check sensor `reachable` status in Hue app
5. Move sensors closer to Bridge (Zigbee range ~30m)

### Duplicate Reading Errors

**Problem**: `UNIQUE constraint failed: device_id, timestamp`

**Solutions**:
1. Check collection interval isn't too fast (min 5 minutes)
2. Verify system clock is accurate (NTP sync)
3. Ensure only one collection process running
4. Check for manual test runs overlapping with automation

### Database Locked

**Problem**: `database is locked`

**Solutions**:
1. Enable WAL mode in config: `journal_mode: "WAL"`
2. Close other SQLite connections (e.g., DB Browser)
3. Check file permissions: `chmod 664 data/temperature.db`
4. Verify database path is correct in config

---

## Quick Reference

### Commands

```bash
# Authentication (one-time)
python source/collectors/hue_auth.py

# Discover sensors
python source/collectors/hue_collector.py --discover

# Collect once (test)
python source/collectors/hue_collector.py --collect-once

# Continuous collection
python source/collectors/hue_collector.py --continuous

# View logs
tail -f logs/hue_collection.log

# Query database
sqlite3 data/temperature.db "SELECT * FROM temperature_readings LIMIT 5;"
```

### File Locations

| File | Path | Purpose |
|------|------|---------|
| Config | `config/config.yaml` | Hue settings, intervals, validation |
| Secrets | `config/secrets.yaml` | API key, Bridge ID (gitignored) |
| Database | `data/temperature.db` | SQLite temperature readings |
| Logs | `logs/hue_collection.log` | Collection activity logs |
| Collector | `source/collectors/hue_collector.py` | Main collection script |
| Auth | `source/collectors/hue_auth.py` | Authentication utility |

### Expected Collection Rates

| Interval | Readings/Hour | Readings/Day | Readings/Week |
|----------|---------------|--------------|---------------|
| 5 min | 12 | 288 | 2,016 |
| 10 min | 6 | 144 | 1,008 |
| 15 min | 4 | 96 | 672 |

**Default**: 5 minutes (288 readings/day per sensor)

---

## Next Steps

1. ✅ Complete Hue integration setup
2. ⏭️ Proceed to **Sprint 2: Google Nest Integration**
3. ⏭️ Configure automated scheduling (Sprint 3)
4. ⏭️ Set up data quality monitoring (Sprint 4)

---

## Support

- **Hue API Documentation**: https://developers.meethue.com/develop/hue-api-v2/
- **phue Library**: https://github.com/studioimaginaire/phue
- **Project Constitution**: `docs/project-outliner.md`
- **Feature Spec**: `specs/002-hue-integration/spec.md`
