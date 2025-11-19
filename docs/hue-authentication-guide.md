# Philips Hue Authentication Guide

## Overview

This guide documents the authentication process for connecting to the Philips Hue Bridge and verifying that credentials remain valid over time.

## Initial Authentication Steps

### 1. Run the Authentication Script

```bash
# Activate virtual environment
source venv/bin/activate

# Option A: Auto-discover bridge
python source/collectors/hue_auth.py

# Option B: Specify bridge IP manually
python source/collectors/hue_auth.py --bridge-ip <HUE_BRIDGE_IP>
```

### 2. Press the Link Button

When prompted, physically press the link button on your Hue Bridge. You have 30 seconds to complete this step.

### 3. Credentials Saved

Upon successful authentication, the script saves:
- **API Key** (username): Stored in `config/secrets.yaml`
- **Bridge ID**: Stored in `config/secrets.yaml`
- **Bridge IP**: Cached by the phue library in `~/.python_hue`

## Verification After 24 Hours

To verify that authentication credentials remain valid:

### Test 1: Discover Sensors

```bash
source venv/bin/activate
python source/collectors/hue_collector.py --discover
```

**Expected Output:**
- Successfully connects to bridge
- Lists all temperature sensors with status and battery level
- Shows device IDs and models

### Test 2: Collect Temperature Readings

```bash
source venv/bin/activate
python source/collectors/hue_collector.py --collect-once
```

**Expected Output:**
- Discovers sensors
- Collects current temperature readings
- Stores readings to database
- Reports collection statistics

## Results from 19 November 2025 Test

### Test Conducted
- **Initial Auth**: 18 November 2025
- **Verification**: 19 November 2025 (24 hours later)
- **Status**: ✅ SUCCESSFUL

### Connection Details
- **Bridge IP**: <HUE_BRIDGE_IP>
- **API Key**: <API_KEY>
- **Bridge ID**: <BRIDGE_ID>

### Sensors Discovered
1. **Utility**
   - Device ID: 00:17:88:01:02:02:b5:21-02-0402
   - Model: SML001
   - Battery: 100%
   - Temperature: 20.29°C

2. **Hall**
   - Device ID: 00:17:88:01:03:28:0f:d0-02-0402
   - Model: SML001
   - Battery: 100%
   - Temperature: 19.83°C

### Key Findings

1. **API Key Persistence**: The API key remains valid 24 hours after creation
2. **No Re-authentication Required**: No need to press the link button again
3. **Automatic IP Resolution**: The phue library caches the bridge IP in `~/.python_hue`
4. **Full Functionality**: All operations (discover, collect, store) work correctly

## Credential Storage

### secrets.yaml
```yaml
hue:
  api_key: <API_KEY>
  bridge_id: <BRIDGE_ID>
```

### phue Cache (~/.python_hue)
The phue library automatically stores:
```json
{
  "<HUE_BRIDGE_IP>": {
    "username": "<API_KEY>"
  }
}
```

## Troubleshooting

### Auto-Discovery Fails

If automatic bridge discovery fails:

```bash
# Use manual IP specification
python source/collectors/hue_auth.py --bridge-ip <your-bridge-ip>
```

### Finding Your Bridge IP

1. Check your router's DHCP client list
2. Use the Philips Hue mobile app (Settings → Bridge → Network)
3. Visit https://discovery.meethue.com/ for automatic detection

### Connection Timeout

If you see "POST Request to <ip>/api timed out":
- Verify the bridge IP is correct
- Ensure bridge is powered on and connected to network
- Check firewall settings

## API Key Lifespan

Based on testing and Philips Hue documentation:
- **Duration**: API keys are long-lived (effectively permanent)
- **Revocation**: Keys remain valid until manually revoked via the bridge
- **Limit**: Up to 40 API keys can be registered per bridge
- **Re-authentication**: Only required if key is manually deleted or bridge is reset

## Security Notes

1. **secrets.yaml** is gitignored and should never be committed
2. API keys have full access to the bridge - treat them as passwords
3. The `~/.python_hue` cache file also contains credentials
4. Consider using environment variables for production deployments

## Continuous Collection

For ongoing temperature monitoring:

```bash
# Run continuous collection (every 5 minutes)
python source/collectors/hue_collector.py --continuous
```

This will:
- Collect readings every 5 minutes (configurable in config.yaml)
- Store all readings to SQLite database
- Log to both console and file
- Run indefinitely until stopped (Ctrl+C)
