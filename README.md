# Home Temperature Monitoring

## Overview
A Python-based system for collecting and storing temperature readings from multiple IoT devices. Uses SQLite for local storage and YAML for configuration.

## Features

### ✅ Philips Hue Temperature Collection (Sprint 1)
- Automatic Hue Bridge discovery and authentication
- Temperature data collection from Hue motion sensors
- 5-minute collection intervals with retry logic
- SQLite database storage with duplicate detection
- Battery level and signal strength monitoring

**Status**: Complete  
**Documentation**: [Hue Integration Quickstart](specs/002-hue-integration/quickstart.md)

### ✅ Amazon Alexa Air Quality Monitor Integration (Sprint 2-3)
- Cookie-based authentication via web UI
- Comprehensive air quality monitoring:
  - Temperature (°C)
  - Humidity (%)
  - PM2.5 particulate matter (µg/m³)
  - VOC - Volatile Organic Compounds (ppb)
  - CO - Carbon Monoxide (ppm)
  - IAQ - Indoor Air Quality Score (0-100)
- GraphQL API for device discovery
- Phoenix State API for real-time readings
- Web UI for easy cookie capture at http://localhost:5001/setup

**Status**: Complete  
**Documentation**: [Amazon AQM Integration Plan](docs/Amazon-Alexa-Air-Quality-Monitoring/amazon-aqm-integration-plan.md)

### 🔜 Upcoming Features
- Google Nest Integration (Sprint 4)
- Weather API Integration (Sprint 5)
- Automated Collection Scheduling (Sprint 6)
- Data Analysis & Visualization (Future)

## Quick Start

### Prerequisites
- Python 3.10+
- Virtual environment activated: `source venv/bin/activate`
- Dependencies installed: `pip install -r requirements.txt`

### 1. Install Dependencies and Browser Binaries
```bash
# Install Python dependencies from requirements.txt
pip install -r requirements.txt

# Install Playwright browser binaries (required for web login automation)
playwright install

# Optional: Install system dependencies for Playwright (Linux/Mac)
playwright install-deps
```

### 2. Start the Web Server (for Amazon AQM Setup)
```bash
# Start Flask server for cookie capture UI
make web-start

# Or manually:
python source/web/app.py

# Then navigate to http://localhost:5001/setup
# Press Ctrl+C to stop the server
```

### 3. Authenticate with Philips Hue Bridge
The first time you connect, authenticate with your Hue Bridge:

```bash
# Automatic discovery (recommended)
make auth
# When prompted, press the physical button on your Hue Bridge

# Or with manual IP:
make auth-ip HUE_IP=192.168.1.105
```

Your Hue Bridge username will be saved to `config/secrets.yaml`.

### 4. Authenticate with Amazon Account (Air Quality Monitor)

**Using Web UI** (Recommended):
```bash
# Start the web server
make web-start

# Open http://localhost:5001/setup in your browser
# Click "Connect Amazon Account" and log in
# Cookies will be automatically saved

# Stop the server
make web-stop
```

**Using CLI** (Alternative):
```bash
python source/collectors/amazon_auth.py --domain amazon.co.uk
```

Cookies are stored in `config/secrets.yaml` under `amazon_aqm.cookies`.

### 5. Discover Devices

```bash
# Discover Philips Hue sensors
make discover

# Discover Amazon AQM devices
make aqm-discover
```

### 6. Collect Temperature & Air Quality Data

**Philips Hue**:
```bash
# Single collection
make collect-once

# Continuous (5-minute intervals, Ctrl+C to stop)
make continuous

# Or directly:
python source/collectors/hue_collector.py --collect-once
python source/collectors/hue_collector.py --continuous
```

**Amazon AQM**:
```bash
# Single collection
make aqm-collect

# Continuous (5-minute intervals, Ctrl+C to stop)
make aqm-continuous

# Test integration (discover + collect + verify)
make aqm-test

# Or directly:
python source/collectors/amazon_aqm_collector_main.py --collect-once
python source/collectors/amazon_aqm_collector_main.py --continuous
```

### 7. Query Data

```bash
# View recent readings (all devices)
make db-view

# View database statistics
make db-stats

# Query specific data
make db-query SQL="SELECT device_id, temperature_celsius, timestamp FROM readings WHERE device_type='hue_sensor' LIMIT 10"

# Using sqlite3 directly
sqlite3 data/readings.db "SELECT device_id, temperature_celsius, humidity_percent FROM readings LIMIT 10;"
```

### 8. Device Registry - Custom Device Names (Phase 9)

The device registry allows you to assign friendly names to your sensors, making readings easier to understand. Device names are stored in a **user-editable YAML file** at `config/device_registry.yaml`.

**Automatic Name Inference**:
When devices are first discovered, they automatically receive descriptive names based on their location and type:
- `Hall Hue Sensor` (from location "Hall" + device type "hue_sensor")
- `Living Room AQM` (from location "Living Room" + device type "alexa_aqm")
- `Utility Nest Thermostat` (from location "Utility" + device type "nest_thermostat")

**Customize Device Names - Three Methods**:

1. **Edit YAML File Directly** (Recommended - Simplest):
   ```bash
   # Open config/device_registry.yaml in any text editor
   nano config/device_registry.yaml
   ```
   
   Find your device and change the `name` field:
   ```yaml
   devices:
     hue:00:17:88:01:02:02:b5:21-02-0402:
       name: Kitchen Temperature Monitor  # ← Edit this
       location: Utility
       device_type: hue_sensor
       model_info: SML001
   ```
   
   Changes take effect immediately on the next collection (no restart needed).

2. **Use Makefile Commands**:
   ```bash
   # List all registered devices
   make devices-list
   
   # Set a custom device name
   make devices-set-name DEVICE_ID="hue:00:17:88:01:02:3a:bc:de-02-0402" NAME="Kitchen Sensor"
   ```

3. **Use Python CLI Directly**:
   ```bash
   # List devices with filtering
   python source/storage/device_manager.py --list-devices
   python source/storage/device_manager.py --list-devices --type hue_sensor
   
   # Set device name
   python source/storage/device_manager.py --set-name "hue:ABC123" "Kitchen Sensor"
   ```

**How it works**:
- Devices are automatically registered in `config/device_registry.yaml` when first discovered
- Custom names appear in collection output: `✅ Kitchen Temperature Monitor: 20.5°C [Battery: 100%]`
- Names persist across restarts and are immediately reflected in new readings
- YAML format is human-readable and safe to edit manually
- Device metadata (first_seen, last_seen, model_info) is tracked automatically

**For detailed documentation**, see [`config/DEVICE_REGISTRY_README.md`](config/DEVICE_REGISTRY_README.md) which covers:
- Complete YAML structure explanation
- Device ID format reference
- Troubleshooting common issues
- Best practices for name management

### 9. Development Commands

```bash
# View logs
make logs

# Follow logs in real-time
make logs-tail

# Clear logs
make logs-clear

# Reset database (development only - loses all data)
make db-reset

# Run tests
make test
make test-discover
make test-full
```

All commands are documented in the Makefile:
```bash
make help
```

## Project Structure
```
source/
├── collectors/           # Data collection modules
│   ├── hue_auth.py      # Hue Bridge authentication
│   └── hue_collector.py # Hue temperature collection
├── storage/             # Database management
│   ├── manager.py       # Database operations
│   └── schema.py        # Schema definitions
├── config/              # Configuration handling
│   ├── loader.py        # Config loader
│   └── validator.py     # Config validation
└── utils/               # Utility modules
    └── logging.py       # Logging utilities

config/
├── config.yaml          # Application configuration
└── secrets.yaml         # API keys and credentials (gitignored)

data/
└── readings.db          # SQLite temperature database

specs/
├── 001-project-foundation/  # Initial setup documentation
└── 002-hue-integration/     # Hue feature specification
```

## Pre-Execution Hook System

This project uses **SpecKit's Pre-Execution Hook** system to prevent common development issues and reduce session failures from ~15-20% to <5%.

### How It Works

Before any SpecKit agent command (`/speckit.implement`, `/speckit.plan`, etc.) starts work, it automatically:

1. **Displays Constitution Reminders**: Shows critical project principles to prevent mistakes
2. **Activates Python venv**: Auto-detects and activates virtual environment
3. **Validates Environment**: Checks required setup before proceeding
4. **Blocks on Errors**: Stops execution if critical issues found (exit 1)
5. **Warns on Issues**: Shows warnings but continues if non-critical (exit 2)

### Exit Code Behavior

| Exit Code | Meaning | Agent Behavior |
|-----------|---------|----------------|
| `0` | Success - all checks passed | Proceed to agent work |
| `1` | Critical failure | **STOP** - fix issue first |
| `2` | Warning - non-critical | Show warning, continue |

### Manual Testing

Test the pre-check script independently:

```bash
# Normal execution (exit 0 expected)
bash .specify/scripts/bash/pre-agent-check.sh
echo $?  # Should show 0

# Deactivate venv and test auto-activation
deactivate
bash .specify/scripts/bash/pre-agent-check.sh  # Should auto-activate
```

### Customization

The pre-check script is located at `.specify/scripts/bash/pre-agent-check.sh`. Customize it to add:

- Additional environment variable checks
- Database connection validation
- API credential verification
- Custom project-specific requirements

**Note**: The pre-check script is optional. If it doesn't exist, agents skip directly to their core work (backward compatible).

### Troubleshooting Pre-Check Failures

**venv activation fails**:
```bash
# Ensure venv exists
python3 -m venv venv

# Manually activate and test
source venv/bin/activate
which python  # Should show path to venv/bin/python
```

**Constitution reminders not showing**:
```bash
# Test helper script directly
bash .specify/scripts/bash/show-constitution-reminders.sh
```

**Pre-check script blocked**:
- Read error message carefully (shows what failed)
- Fix the reported issue before re-running agent
- For persistent issues, temporarily rename script to bypass: `mv .specify/scripts/bash/pre-agent-check.sh{,.bak}`

For more details, see:
- **Implementation Spec**: `specs/006-pre-execution-hook/spec.md`
- **Testing Instructions**: `specs/006-pre-execution-hook/TESTING_INSTRUCTIONS.md`
- **Template for New Projects**: `.specify/templates/pre-agent-check.sh.template`

---

## Documentation
- [Project Constitution](docs/project-outliner.md) - Development principles and constraints
- [Hue Integration Guide](specs/002-hue-integration/quickstart.md) - Complete Hue setup walkthrough
- [Amazon AQM Integration Guide](specs/004-alexa-aqm-integration/quickstart.md) - Amazon Air Quality Monitor setup
- [Feature Specifications](specs/) - Detailed feature documentation

## Troubleshooting

### Amazon AQM Issues

**Cookie Authentication Failures**
- **Problem**: "Invalid or missing cookies" error
- **Solution**: 
  1. Start web server: `python source/web/app.py`
  2. Navigate to http://localhost:5001/setup
  3. Complete Amazon login flow
  4. Verify cookies saved in `config/secrets.yaml` under `amazon_aqm.cookies`

**Expired Cookies (24-hour lifespan)**
- **Problem**: "Unauthenticated call" errors after working previously
- **Solution**: Re-run web UI setup to refresh cookies (repeat steps above)

**No Devices Found**
- **Problem**: Device discovery returns empty list
- **Checks**:
  - Verify device is online in Alexa app
  - Ensure device is registered to the same Amazon account used for login
  - Check device appears at https://alexa.amazon.co.uk/spa/index.html
  - Confirm `domain` in `config/config.yaml` matches your Amazon region

**Data Collection Failures**
- **Problem**: No readings returned from device
- **Checks**:
  - Device has latest firmware (update via Alexa app)
  - Sensor capabilities vary by model (all have temp/humidity, some have PM2.5/VOC/CO)
  - Network connectivity to Amazon services
  - Check logs with DEBUG level: `--log-level DEBUG` flag

**Database Errors**
- **Problem**: Duplicate timestamp errors
- **Explanation**: Expected behavior - UNIQUE constraint prevents duplicate readings
- **Problem**: Missing columns (co_ppm, iaq_score)
- **Solution**: Schema auto-migrates on first insert; verify with `sqlite3 data/readings.db ".schema readings"`

**Rate Limiting**
- **Problem**: API throttling or timeout errors
- **Solution**: 
  - Increase `collection_interval` to 300+ seconds (5+ minutes)
  - Adjust `timeout_seconds` in config (default: 30)
  - Built-in exponential backoff handles retries automatically

### Hue Integration Issues

**Bridge Discovery Problems**
- **Problem**: Cannot find Hue Bridge on network
- **Solution**:
  1. Ensure bridge is powered on and connected to network
  2. Check bridge IP address in Hue app
  3. Manually set `bridge_ip` in `config/config.yaml`

**Authentication Failures**
- **Problem**: "Link button not pressed" error
- **Solution**: 
  1. Press physical button on Hue Bridge
  2. Run authentication within 30 seconds
  3. Username will be saved in `config/secrets.yaml`

**No Sensors Found**
- **Problem**: Motion sensors not discovered
- **Checks**:
  - Sensors are paired with bridge (visible in Hue app)
  - Sensors have fresh batteries
  - Bridge firmware is up to date

### Database Issues

**Database Locked**
- **Problem**: "Database is locked" error
- **Solution**:
  - Ensure no other processes accessing database
  - WAL mode enabled by default for concurrent access
  - Check for stale lock files in `data/`

**Schema Migration Failures**
- **Problem**: Errors during schema updates
- **Solution**:
  1. Backup database: `cp data/readings.db data/readings.db.backup`
  2. Check current schema: `sqlite3 data/readings.db ".schema"`
  3. Migration auto-runs on first insert with new columns
  4. Verify migration: `sqlite3 data/readings.db "PRAGMA table_info(readings);"`

### General Issues

**Configuration Errors**
- **Problem**: Invalid YAML syntax
- **Solution**: Validate YAML structure at https://www.yamllint.com/
- **Problem**: Missing required fields
- **Solution**: Check `config/config.yaml.example` for complete structure

**Network Connectivity**
- **Problem**: Timeouts or connection refused
- **Checks**:
  - Devices on same network/VLAN as host
  - Firewall rules allow outbound HTTPS (Amazon APIs)
  - DNS resolution working (test: `ping alexa.amazon.co.uk`)

**Log Analysis**
- Enable DEBUG logging: Set `log_level: DEBUG` in `config/config.yaml`
- Check log files in `logs/` directory
- Look for patterns: authentication failures, API errors, validation issues

## Usage
- Activate virtual environment
- Run scripts in source/
- Data stored in data/readings.db
- Configuration in config/config.yaml
