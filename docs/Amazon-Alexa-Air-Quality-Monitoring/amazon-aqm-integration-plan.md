# Amazon AQM Database Integration Plan

## Overview
Integrate the working Amazon Air Quality Monitor collector into the existing database storage system.

---

## Current State Analysis

### ✅ What's Working
1. **AmazonAQMCollector** (`source/collectors/amazon_collector.py`):
   - Device discovery via GraphQL
   - Data collection via correct Phoenix state API endpoint
   - Returns readings: `temperature_celsius`, `humidity_percent`, `voc_ppb`, `co_ppm`, `iaq_score`, `pm25_ugm3`, `connectivity`

2. **Database Schema** (`source/storage/schema.py`):
   - Already has columns for AQM data: `pm25_ugm3`, `voc_ppb`, `co2_ppm`, `humidity_percent`
   - Has `device_type` enum including `'alexa_aqm'`
   - Missing: `co_ppm` (we have CO not CO2), `iaq_score`

3. **Storage Manager** (`source/storage/manager.py`):
   - `insert_temperature_reading()` with retry logic
   - UNIQUE constraint on `(device_id, timestamp)`
   - Field validation

### ❌ What's Missing
1. Schema needs new columns: `co_ppm`, `iaq_score`
2. No Amazon AQM collector configuration in `config.yaml`
3. No main collection script for AQM (like `hue_collector.py`)
4. No integration with continuous collection loop

---

## Implementation Plan

### Phase 1: Database Schema Updates ⏱️ 5 min

**File**: `source/storage/schema.py`

**Changes**:
```sql
-- Add CO (carbon monoxide) column
co_ppm REAL CHECK(co_ppm IS NULL OR co_ppm >= 0),

-- Add Indoor Air Quality score column  
iaq_score REAL CHECK(iaq_score IS NULL OR (iaq_score >= 0 AND iaq_score <= 100)),
```

**File**: `source/storage/manager.py`

**Changes**:
- Add `'co_ppm'` and `'iaq_score'` to `required_cols` in `init_schema()`
- Add migration logic for existing databases

**Validation**: Run migration on test database

---

### Phase 2: Cookie Capture Web Interface ⏱️ 15 min

**Status**: ✅ Already Implemented!

**Existing Implementation**:
- `source/web/app.py`: Flask web server with Amazon login endpoint
- `source/web/templates/setup.html`: User-friendly setup page
- `source/web/templates/base.html`: Base template with navigation

**Current Functionality**:
1. User navigates to `http://localhost:5001/setup`
2. Clicks "Connect Amazon Account" button
3. Playwright opens browser for Amazon login
4. After login, cookies auto-saved to `config/secrets.yaml`
5. Web UI shows success with cookie count

**Integration Needed**:
- Update `source/collectors/amazon_auth.py` to add `run_amazon_login()` function (currently only in old docs)
- Verify Flask app works with updated collector
- Add web UI documentation to README

**Code to Add** to `source/collectors/amazon_auth.py`:

```python
def run_amazon_login(domain: str = "amazon.co.uk") -> Optional[Dict[str, str]]:
    """
    Launches Playwright to log in to Amazon and retrieve cookies.
    Used by web interface for cookie capture.
    
    Args:
        domain: Amazon domain (default: amazon.co.uk)
        
    Returns:
        dict: Cookie name/value pairs, or None if failed
    """
    capturer = AmazonCookieCapture(domain=domain, headless=False)
    cookies = capturer.capture_cookies(timeout=300)
    return cookies
```

**Testing**:
```bash
# Start web server
python source/web/app.py

# Open browser
open http://localhost:5001/setup

# Click "Connect Amazon Account"
# Log in when browser opens
# Verify success message shows cookie count
```

---

### Phase 3: Configuration Setup ⏱️ 10 min

**File**: `config/config.yaml`

**Add section**:
```yaml
collectors:
  # ... existing hue, nest, weather ...
  
  amazon_aqm:
    enabled: false  # Disabled by default (requires cookie auth)
    domain: "alexa.amazon.co.uk"  # UK domain (adjust per region)
    device_serial: null  # Auto-discover if null, or specify: "GAJ23005314600H3"
    timeout_seconds: 30
    collection_interval: 300  # 5 minutes (same as Hue)
    retry_attempts: 3
    retry_backoff_base: 1.0
    max_timeout: 120
    
    # Device mapping
    device_locations:
      "GAJ23005314600H3": "Living Room"  # Map serial to location
    
    fallback_location: "Unknown"  # If device not in mapping
    
    # Validation ranges (optional - already in schema)
    temperature_min: 0.0
    temperature_max: 40.0
    humidity_min: 0.0
    humidity_max: 100.0
    iaq_min: 0
    iaq_max: 100
    
    # What to collect
    collect_temperature: true
    collect_humidity: true
    collect_pm25: true
    collect_voc: true
    collect_co: true
    collect_iaq: true
    collect_connectivity: false  # Don't store as separate field
    collect_raw_response: false  # Save full API response in raw_response column
```

**File**: `config/secrets.yaml`

**Verify section exists**:
```yaml
amazon_aqm:
  cookies:
    # Captured via Playwright authentication
    session-id: "..."
    session-token: "..."
    csrf: "..."
    # ... 18 cookies total
```

---

### Phase 4: Collector Enhancement ⏱️ 20 min

**File**: `source/collectors/amazon_collector.py`

**Add methods** (similar to `hue_collector.py` pattern):

```python
def format_reading_for_db(self, entity_id: str, serial: str, readings: dict, config: dict) -> dict:
    """
    Format AQM readings for database insertion.
    
    Args:
        entity_id: Device entity ID
        serial: Device serial number
        readings: Raw readings from get_air_quality_readings()
        config: Configuration dict
        
    Returns:
        dict: Formatted reading ready for database
    """
    # Get location from config mapping
    locations = config.get('amazon_aqm', {}).get('device_locations', {})
    location = locations.get(serial, config.get('amazon_aqm', {}).get('fallback_location', 'Unknown'))
    
    # Build device_id (format: alexa:serial)
    device_id = f"alexa:{serial}"
    
    # Format reading
    db_reading = {
        'timestamp': readings['timestamp'],
        'device_id': device_id,
        'temperature_celsius': readings.get('temperature_celsius'),
        'location': location,
        'device_type': 'alexa_aqm',
        'humidity_percent': readings.get('humidity_percent'),
        'pm25_ugm3': readings.get('pm25_ugm3'),
        'voc_ppb': readings.get('voc_ppb'),
        'co_ppm': readings.get('co_ppm'),
        'iaq_score': readings.get('iaq_score'),
    }
    
    # Add raw response if configured
    if config.get('amazon_aqm', {}).get('collect_raw_response', False):
        import json
        db_reading['raw_response'] = json.dumps(readings)
    
    return db_reading


async def collect_and_store(cookies: dict, config: dict, db_manager) -> bool:
    """
    Convenience function to collect AQM data and store in database.
    
    Args:
        cookies: Amazon authentication cookies
        config: Configuration dictionary
        db_manager: DatabaseManager instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        collector = AmazonAQMCollector(cookies, config)
        
        # Discover devices
        devices = await collector.list_devices()
        
        if not devices:
            logger.warning("No Amazon Air Quality Monitors found")
            return False
        
        # Collect from each device
        success_count = 0
        for device in devices:
            entity_id = device['entity_id']
            serial = device['device_serial']
            
            # Get readings
            readings = await collector.get_air_quality_readings(entity_id)
            
            if not readings:
                logger.error(f"Failed to get readings from {serial}")
                continue
            
            # Validate
            errors = collector.validate_readings(readings)
            if errors:
                logger.warning(f"Validation errors for {serial}: {errors}")
                # Continue anyway - store what we have
            
            # Format for database
            db_reading = format_reading_for_db(entity_id, serial, readings, config)
            
            # Insert to database
            if db_manager.insert_temperature_reading(db_reading):
                logger.info(f"Stored reading from {serial} ({device.get('friendly_name', 'Unknown')})")
                success_count += 1
            else:
                logger.debug(f"Duplicate reading from {serial}, skipped")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error collecting AQM data: {e}", exc_info=True)
        return False
```

---

### Phase 5: Main Collection Script ⏱️ 30 min

**New File**: `source/collectors/amazon_aqm_collector_main.py`

**Purpose**: Standalone script for AQM collection (mirrors `hue_collector.py` structure)

**Features**:
- `--discover`: List all AQM devices
- `--collect-once`: Single collection run
- `--continuous`: Continuous collection loop
- Cookie validation
- Error handling and logging

**Key sections**:
```python
def discover_devices(cookies: dict, config: dict):
    """List all Amazon AQM devices."""
    
def collect_once(cookies: dict, config: dict, db_manager):
    """Collect data once and store."""
    
def collect_continuous(cookies: dict, config: dict, db_manager):
    """Continuous collection loop."""
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--discover', action='store_true')
    parser.add_argument('--collect-once', action='store_true')
    parser.add_argument('--continuous', action='store_true')
    # ...
```

---

### Phase 6: Integration Testing ⏱️ 20 min

**Test Cases**:

1. **Schema Migration**:
   ```bash
   # Test on existing database
   python -c "from source.storage.manager import DatabaseManager; DatabaseManager()"
   # Verify new columns added
   sqlite3 data/readings.db "PRAGMA table_info(readings)" | grep -E "co_ppm|iaq_score"
   ```

2. **Single Collection**:
   ```bash
   python source/collectors/amazon_aqm_collector_main.py --collect-once
   # Verify reading inserted
   sqlite3 data/readings.db "SELECT * FROM readings WHERE device_type='alexa_aqm' ORDER BY timestamp DESC LIMIT 1"
   ```

3. **Validation**:
   ```python
   # Test out-of-range values rejected
   # Test duplicate detection (same timestamp)
   # Test retry logic (simulate database lock)
   ```

4. **Continuous Collection**:
   ```bash
   # Run for 15 minutes, verify readings collected every 5 min
   timeout 900 python source/collectors/amazon_aqm_collector_main.py --continuous
   ```

---

### Phase 7: Documentation ⏱️ 15 min

**Update Files**:

1. **README.md**:
   - Add Amazon AQM to supported collectors
   - Document cookie authentication requirement
   - Add setup instructions

2. **docs/quickstart.md** (if exists):
   - Amazon AQM setup section
   - Cookie capture instructions (reference `amazon_auth.py`)

3. **CHANGELOG.md**:
   - Document new collector addition
   - Schema changes
   - Configuration options

---

## Implementation Checklist

- [ ] **Phase 1**: Update database schema
  - [ ] Add `co_ppm` column to schema.sql
  - [ ] Add `iaq_score` column to schema.sql
  - [ ] Update `manager.py` migration logic
  - [ ] Test migration on existing DB

- [ ] **Phase 2**: Cookie capture web interface
  - [ ] Add `run_amazon_login()` to `amazon_auth.py`
  - [ ] Test web UI at http://localhost:5001/setup
  - [ ] Verify cookies saved to secrets.yaml
  - [ ] Document web UI usage

- [ ] **Phase 3**: Configuration setup
  - [ ] Add `amazon_aqm` section to config.yaml
  - [ ] Verify secrets.yaml has cookies
  - [ ] Document configuration options

- [ ] **Phase 4**: Enhance collector
  - [ ] Add `format_reading_for_db()` method
  - [ ] Add `collect_and_store()` method
  - [ ] Test formatting logic

- [ ] **Phase 5**: Create main script
  - [ ] Create `amazon_aqm_collector_main.py`
  - [ ] Implement `--discover` mode
  - [ ] Implement `--collect-once` mode
  - [ ] Implement `--continuous` mode
  - [ ] Add error handling and logging

- [ ] **Phase 6**: Integration testing
  - [ ] Test schema migration
  - [ ] Test web UI cookie capture
  - [ ] Test single collection
  - [ ] Test validation
  - [ ] Test continuous collection
  - [ ] Test error scenarios

- [ ] **Phase 7**: Documentation
  - [ ] Update README.md with web UI instructions
  - [ ] Update quickstart guide
  - [ ] Update CHANGELOG.md
  - [ ] Add inline code comments

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER AUTHENTICATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Option 1: Web UI (Recommended)                                 │
│  ┌──────────────────┐                                           │
│  │ User Browser     │──────> http://localhost:5001/setup        │
│  │ - Clicks button  │                                           │
│  └────────┬─────────┘                                           │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │ Flask Web Server │────────>│ amazon_auth.py   │             │
│  │ /api/amazon/login│         │ run_amazon_login()│             │
│  └────────┬─────────┘         └────────┬─────────┘             │
│           │                             │                       │
│           │                    ┌────────▼─────────┐            │
│           │                    │ Playwright       │            │
│           │                    │ - Opens browser  │            │
│           │                    │ - User logs in   │            │
│           │                    │ - Captures 18    │            │
│           │                    │   cookies        │            │
│           │                    └────────┬─────────┘            │
│           │                             │                       │
│           │                             ▼                       │
│           │                    ┌─────────────────┐             │
│           └───────────────────>│ secrets.yaml    │             │
│                                 │ amazon_aqm:     │             │
│                                 │   cookies: {...}│             │
│                                 └─────────────────┘             │
│                                                                  │
│  Option 2: CLI                                                  │
│  $ python source/collectors/amazon_auth.py                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────────────────┐                                         │
│ │ Amazon AQM Device   │                                         │
│ │ (WiFi Connected)    │                                         │
│ └──────────┬──────────┘                                         │
│            │                                                     │
│            │ Sends data to                                      │
│            ▼                                                     │
│ ┌─────────────────────┐                                         │
│ │ Amazon Alexa Cloud  │                                         │
│ │ (alexa.amazon.co.uk)│                                         │
│ └──────────┬──────────┘                                         │
│            │                                                     │
│            │ Cookie-authenticated API                           │
│            │ POST /api/phoenix/state                            │
│            ▼                                                     │
│ ┌─────────────────────┐                                         │
│ │ AmazonAQMCollector  │                                         │
│ │ - list_devices()    │                                         │
│ │ - get_readings()    │                                         │
│ └──────────┬──────────┘                                         │
│            │                                                     │
│            │ format_reading_for_db()                            │
│            ▼                                                     │
│ ┌─────────────────────┐                                         │
│ │ DatabaseManager     │                                         │
│ │ - insert_reading()  │                                         │
│ │ - validation        │                                         │
│ │ - retry logic       │                                         │
│ └──────────┬──────────┘                                         │
│            │                                                     │
│            ▼                                                     │
│ ┌─────────────────────┐                                         │
│ │ SQLite Database     │                                         │
│ │ data/readings.db    │                                         │
│ │ - readings table    │                                         │
│ └─────────────────────┘                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Risk Assessment

### Potential Issues

1. **Cookie Expiration**:
   - **Risk**: High - Cookies expire after ~24 hours
   - **Mitigation**: 
     - Add cookie validation before collection
     - Log clear error message when auth fails
     - Document cookie refresh process
     - Consider automated cookie refresh (future enhancement)

2. **API Rate Limiting**:
   - **Risk**: Medium - Amazon may throttle requests
   - **Mitigation**:
     - 5-minute collection interval (same as Hue)
     - Exponential backoff on errors
     - Monitor for 429 responses

3. **Schema Migration**:
   - **Risk**: Low - Adding columns to existing table
   - **Mitigation**:
     - Test on copy of production DB first
     - Columns nullable (won't break existing rows)
     - Backup DB before migration

4. **Data Quality**:
   - **Risk**: Medium - Unknown sensor values (instance 7)
   - **Mitigation**:
     - Store unknown values as `unknown_7` for analysis
     - Validate all known sensors
     - Log unexpected data formats

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Schema | 5 min | None |
| Phase 2: Web UI | 15 min | Phase 1 |
| Phase 3: Config | 10 min | Phase 1, 2 |
| Phase 4: Collector | 20 min | Phase 1, 2, 3 |
| Phase 5: Main Script | 30 min | Phase 4 |
| Phase 6: Testing | 20 min | Phase 5 |
| Phase 7: Docs | 15 min | Phase 6 |
| **Total** | **115 min** (~2 hours) | - |

---

## Success Criteria

- ✅ Schema updated with new columns (`co_ppm`, `iaq_score`)
- ✅ Web UI working for cookie capture (http://localhost:5001/setup)
- ✅ `run_amazon_login()` function added to `amazon_auth.py`
- ✅ Configuration added to `config.yaml`
- ✅ `collect_and_store()` function working
- ✅ Main script created with all modes
- ✅ Readings successfully stored in database
- ✅ Validation working correctly
- ✅ Continuous collection runs without errors
- ✅ Web UI properly documented
- ✅ Documentation updated
- ✅ All tests passing

---

## Next Steps After Integration

1. **Web Dashboard**: Add AQM data to web visualization
2. **Alerting**: Set up alerts for poor air quality (IAQ < 50)
3. **Analysis**: Compare AQM data with Hue temperature sensors
4. **Automation**: Trigger actions based on air quality readings
5. **Cookie Refresh**: Automate cookie renewal process

---

## Notes

- Schema already supports most AQM fields (forward-thinking design!)
- Only 2 new columns needed: `co_ppm` and `iaq_score`
- Pattern matches existing Hue collector (easy to maintain)
- Cookie authentication is manual but working
- Total integration time: ~2 hours
