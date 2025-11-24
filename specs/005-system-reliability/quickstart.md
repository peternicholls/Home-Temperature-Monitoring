# Quickstart: Production-Ready System Reliability

## Overview

This guide covers operational procedures for the Production-Ready System Reliability features introduced in Sprint 005. These features ensure the temperature monitoring system can run unattended for extended periods (7+ days) with comprehensive error handling, health validation, and performance monitoring.

## Health Check Usage

### Running Health Checks

**Basic Usage**:
```bash
# Run comprehensive health check (completes in <15 seconds)
python source/health_check.py

# Expected output (all pass):
# ✅ Database WAL Mode: Enabled
# ✅ Configuration: Valid
# ✅ Secrets: Present
# ✅ Database Write: Success
# ✅ Log Rotation: Configured
# ✅ Hue Bridge: Connected
# ✅ Amazon AQM: Connected
# 
# Health Check: PASS (all checks passed)
# Exit code: 0
```

**Exit Codes**:
- `0`: All checks passed - system ready for production
- `1`: Some checks failed - review errors and remediation guidance
- `2`: Critical failure - system cannot operate

**Integration with Deployment**:
```bash
# CI/CD pipeline integration
python source/health_check.py || exit 1

# Timeout enforcement (15 seconds)
timeout 15s python source/health_check.py || exit 1

# Cron job for regular health monitoring
0 6 * * * cd /path/to/project && python source/health_check.py || mail -s "Health Check Failed" admin@example.com
```

### Component Validators

Each health check component validates a critical system dependency:

1. **Database WAL Mode**: 
   - Validates Write-Ahead Logging enabled
   - Checks checkpoint interval configured
   - Ensures concurrent access support
   - **Failure**: Delete database and recreate

2. **Configuration**:
   - Validates `config/config.yaml` structure
   - Checks required fields present
   - Verifies collection intervals configured
   - **Failure**: Review `config/config.yaml.example`

3. **Secrets**:
   - Confirms `config/secrets.yaml` exists
   - Validates Hue Bridge username present
   - Checks Amazon cookies present (if configured)
   - **Failure**: Run authentication (`make auth`, `make web-start`)

4. **Database Write**:
   - Tests write operation with rollback
   - Validates file permissions (writable)
   - Checks disk space available
   - **Failure**: Fix permissions or free disk space

5. **Log Rotation**:
   - Validates log directory writable
   - Checks rotation thresholds configured (10MB per file, 60MB total)
   - Ensures backup count set (5 backups)
   - **Failure**: Create `logs/` directory or fix permissions

6. **Hue Bridge Connectivity**:
   - Tests network connection to bridge
   - Validates authentication
   - Confirms sensor discovery
   - **Failure**: Check network, verify IP address, re-authenticate

7. **Amazon AQM Connectivity**:
   - Validates cookies not expired
   - Tests GraphQL API access
   - Confirms device discovery
   - **Failure**: Re-authenticate via web UI

### Troubleshooting Health Check Failures

| Component | Common Failures | Remediation |
|-----------|-----------------|-------------|
| WAL Mode | Database created without WAL | `rm data/readings.db` and recreate |
| Configuration | Missing required fields | Compare with `config/config.yaml.example` |
| Secrets | File not found | Run `make auth` and `make web-start` |
| Database Write | Read-only file system | `chmod 644 data/readings.db` |
| Log Rotation | Directory not writable | `mkdir -p logs && chmod 755 logs` |
| Hue Bridge | Network unreachable | Verify `bridge_ip` in config, check network |
| Amazon AQM | Expired cookies | Re-run web UI: `make web-start` |

## Monitoring Alert Files

### OAuth Token Refresh Alert

**Alert File**: `data/ALERT_TOKEN_REFRESH_NEEDED.txt`

**Trigger**: Amazon AQM collector detects permanent authentication failure

**Resolution Steps**:
1. Start web server: `make web-start`
2. Open http://localhost:5001/setup in browser
3. Click "Connect Amazon Account" and log in
4. Verify cookies saved to `config/secrets.yaml`
5. Stop web server (Ctrl+C)
6. Next collection cycle will auto-clear alert file

## Performance Baseline Guidance

### Capturing Baseline Metrics

**Before Optimization**:
```bash
# Capture baseline performance for Hue collector
python source/utils/performance.py --capture-baseline --collector hue
```

### Optimization Targets

**Sprint 005 Targets**:
- **Cycle Duration**: 30% improvement (faster collection)
- **Network Payload**: 50% reduction (smaller data transfer)

## Device Naming CLI Commands

### List Devices

```bash
# List all registered devices
python source/storage/device_manager.py --list-devices

# Or use Makefile
make devices-list
```

### Set Device Name

```bash
# Set custom device name
python source/storage/device_manager.py --set-name "hue:00:17:88:01:02:02:b5:21-02-0402" "Kitchen Sensor"

# Or use Makefile
make devices-set-name DEVICE_ID="hue:..." NAME="Kitchen Sensor"
```

### Amend Device Name (with History Update)

```bash
# Update device name for new readings only
python source/storage/device_manager.py --amend-name "hue:..." "New Name"

# Update device name AND historical readings
python source/storage/device_manager.py --amend-name "hue:..." "New Name" --recursive
```

## Integration Scenarios

### Scenario 1: 24-Hour Continuous Operation Test

**Setup**:
```bash
# Terminal 1: Hue collector
python source/collectors/hue_collector.py --continuous

# Terminal 2: Amazon AQM collector
python source/collectors/amazon_aqm_collector_main.py --continuous
```

**Monitoring**:
```bash
# Monitor logs in real-time
tail -f logs/temperature_monitoring.log

# Check for database lock errors
grep "database is locked" logs/temperature_monitoring.log

# Check for retry events
grep "Retry attempt" logs/temperature_monitoring.log
```

**Success Criteria**:
- Zero data loss (100% of readings stored)
- Zero database locked errors
- Log disk usage under 60MB
- No manual intervention required

### Scenario 2: Network Failure Simulation

**Simulation**: Disconnect network temporarily and observe retry behavior

```bash
# Check logs for retry events
grep "Retry attempt" logs/temperature_monitoring.log
```

### Scenario 3: OAuth Token Expiration

**Simulation**:
```bash
# Corrupt Amazon cookies in config/secrets.yaml
# Run collection cycle
python source/collectors/amazon_aqm_collector_main.py --collect-once

# Check for alert file
ls -l data/ALERT_TOKEN_REFRESH_NEEDED.txt
```

**Resolution**: Follow alert file instructions to re-authenticate

### Scenario 4: Health Check Validation

**Test missing configuration**:
```bash
mv config/config.yaml config/config.yaml.backup
python source/health_check.py
# Expected: Exit 2 (critical failure)
mv config/config.yaml.backup config/config.yaml
```

## Quick Reference

### Daily Operations

```bash
# Morning health check
python source/health_check.py

# Start continuous collection
make continuous
make aqm-continuous

# Check for alerts
ls -l data/ALERT_*.txt 2>/dev/null || echo "No alerts"

# View recent readings
make db-view
```

### Troubleshooting Commands

```bash
# View logs
make logs-tail

# Check disk usage
du -sh logs/ data/

# Run health check
python source/health_check.py

# List devices
make devices-list
```

---

**Sprint**: 005-system-reliability  
**Last Updated**: 23 November 2025  
**Documentation Version**: 1.0
