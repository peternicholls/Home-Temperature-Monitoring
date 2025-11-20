````markdown
# Quickstart: Alexa AQM Integration

## Prerequisites
- Python 3.10+
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Ensure `config/secrets.yaml` exists and is gitignored
- Ensure SQLite database is initialized for readings/logs

## Setup

### 1. Configure Amazon AQM

Add Amazon AQM configuration to `config/config.yaml`:

```yaml
collectors:
  amazon_aqm:
    enabled: true
    domain: "amazon.co.uk"  # or amazon.com, amazon.de, etc.
    device_serial: "GAJ23005314600H3"  # Optional, will auto-discover if not set
    timeout_seconds: 30
    collection_interval: 300  # 5 minutes
    retry_attempts: 3
    retry_backoff_base: 1.0
    max_timeout: 120
    
    # Device location mapping (for database storage)
    device_locations:
      "GAJ23005314600H3": "Living Room"
    
    # Sensor collection toggles
    collect_temperature: true
    collect_humidity: true
    collect_pm25: true
    collect_voc: true
    collect_co: true
    collect_iaq: true
```

### 2. Configure Secrets

Ensure `config/secrets.yaml` exists with Amazon AQM cookies structure:

```yaml
amazon_aqm:
  cookies:
    session-id: ""
    session-token: ""
    csrf: ""
    # ... (up to 18 cookies total - will be populated by web UI)
```

## Authentication

Use the web UI to capture Amazon cookies:

```bash
# Start the web server
python source/web/app.py

# Navigate to http://localhost:5001/setup
# Click "Start Amazon Login"
# Complete the login process in the browser
# Cookies will be automatically saved to config/secrets.yaml
```

Programmatic cookie validation:

```python
from source.collectors.amazon_auth import validate_amazon_cookies, check_cookie_expiration
from source.config.loader import load_config

config = load_config()
cookies = config.get('amazon_aqm', {}).get('cookies', {})

# Validate cookie structure
if validate_amazon_cookies(cookies):
    print("✅ Cookies are valid")
    
    # Check expiration (24-hour window)
    if check_cookie_expiration(cookies):
        print("✅ Cookies are fresh")
    else:
        print("⚠️ Cookies may be expired - re-authenticate via web UI")
else:
    print("❌ Invalid cookies - run web UI setup")
```

## Device Access

```python
import asyncio
from source.collectors.amazon_collector import AmazonAQMCollector
from source.config.loader import load_config
import yaml

async def main():
    # Load configuration
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Load cookies from secrets
    with open('config/secrets.yaml', 'r') as f:
        secrets = yaml.safe_load(f)
    
    cookies = secrets.get('amazon_aqm', {}).get('cookies', {})
    
    if not cookies:
        print("❌ No Amazon cookies found in config/secrets.yaml")
        print("Please run: python source/web/app.py and use the web UI to authenticate")
        return
    
    # Initialize collector with cookies and config
    collector = AmazonAQMCollector(cookies=cookies, config=config)
    
    # List all AQM devices
    devices = await collector.list_devices()
    
    print(f"Found {len(devices)} air quality monitor(s):")
    for device in devices:
        print(f"\n  Device: {device['friendly_name']}")
        print(f"    Device ID: {device['device_id']}")
        print(f"    Entity ID: {device['entity_id']}")
        print(f"    Serial: {device['device_serial']}")
        print(f"    Capabilities: {len(device.get('capabilities', []))} sensors")

asyncio.run(main())
```

## Data Retrieval

### Method 1: Using collect_and_store() - Recommended

```python
import asyncio
from source.collectors.amazon_collector import AmazonAQMCollector
from source.storage.manager import DatabaseManager
from source.config.loader import load_config
from source.collectors.amazon_auth import validate_amazon_cookies

async def main():
    config = load_config()
    
    # Validate cookies before starting
    cookies = config.get('amazon_aqm', {}).get('cookies', {})
    if not validate_amazon_cookies(cookies):
        print("❌ Invalid or missing Amazon cookies - run web UI setup first")
        return
    
    # Initialize collector and database
    collector = AmazonAQMCollector(config)
    db = DatabaseManager(config=config)
    
    try:
        # Collect and store in one call - handles discovery, collection, validation, and storage
        success = await collector.collect_and_store(db)
        
        if success:
            print("✅ Data collected and stored successfully")
        else:
            print("❌ Collection or storage failed - check logs")
    finally:
        db.close()

asyncio.run(main())
```

### Method 2: Manual Collection with format_reading_for_db()

```python
import asyncio
import yaml
from source.collectors.amazon_collector import AmazonAQMCollector
from source.storage.manager import DatabaseManager

async def main():
    # Load config and secrets
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    with open('config/secrets.yaml', 'r') as f:
        secrets = yaml.safe_load(f)
    
    cookies = secrets.get('amazon_aqm', {}).get('cookies', {})
    
    if not cookies:
        print("❌ No cookies found - authenticate via web UI first")
        return
    
    # Initialize collector
    collector = AmazonAQMCollector(cookies=cookies, config=config)
    
    # Discover devices
    devices = await collector.list_devices()
    if not devices:
        print("❌ No devices found")
        return
    
    device = devices[0]
    print(f"Found device: {device['friendly_name']} ({device['device_id']})")
    
    # Collect readings
    readings = await collector.get_air_quality_readings(entity_id=device['entity_id'])
    
    if not readings:
        print("❌ Failed to collect readings")
        return
    
    print(f"✅ Collected readings:")
    print(f"  Temperature: {readings.get('temperature_celsius')}°C")
    print(f"  Humidity: {readings.get('humidity_percent')}%")
    print(f"  PM2.5: {readings.get('pm25_ugm3')} µg/m³")
    print(f"  VOC: {readings.get('voc_ppb')} ppb")
    print(f"  CO: {readings.get('co_ppm')} ppm")
    print(f"  IAQ Score: {readings.get('iaq_score')}")
    
    # Validate readings
    errors = collector.validate_readings(readings)
    if errors:
        print(f"⚠️ Validation warnings: {errors}")
    
    # Format for database insertion
    reading_record = collector.format_reading_for_db(
        entity_id=device['entity_id'],
        serial=device['device_serial'],
        readings=readings,
        config=config
    )
    
    if not reading_record:
        print("❌ Failed to format readings")
        return
    
    # Store in database
    db = DatabaseManager(config=config)
    try:
        success = db.insert_temperature_reading(reading_record)
        if success:
            print("✅ Readings stored in database")
            print(f"  Device: {reading_record['device_id']}")
            print(f"  Location: {reading_record.get('location', 'unknown')}")
        else:
            print("⚠️ Duplicate reading or storage error")
    finally:
        db.close()

asyncio.run(main())
```

### Method 3: Using the Main Script (Production)

```bash
# Single collection run
python source/collectors/amazon_aqm_collector_main.py --collect-once

# Continuous collection (5-minute intervals)
python source/collectors/amazon_aqm_collector_main.py --continuous

# Discover devices
python source/collectors/amazon_aqm_collector_main.py --discover
```

## Testing

Run unit tests:

```bash
pytest tests/test_amazon_aqm.py -v
```

Run with coverage:

```bash
pytest tests/test_amazon_aqm.py --cov=source/collectors --cov-report=html
```

Manual testing script:

```python
import asyncio
from source.collectors.amazon_aqm_collector_main import discover_devices, collect_once

async def main():
    # Test device discovery
    print("Testing device discovery...")
    await discover_devices()
    
    # Test single collection
    print("\nTesting data collection...")
    await collect_once()

asyncio.run(main())
```

## Troubleshooting

### Authentication Issues
- **Error: Invalid or missing cookies**
  - Solution: Run web UI setup at http://localhost:5001/setup
  - Verify `config/secrets.yaml` has populated `amazon_aqm.cookies` section
  - Check cookies have `session-id` and `session-token` at minimum

- **Error: Unauthenticated call**
  - Solution: Cookies may be expired (24-hour lifespan)
  - Re-run web UI setup to refresh cookies
  - Check cookie domain matches your Amazon domain (.amazon.co.uk, .amazon.com, etc.)

### Device Access Issues
- **No devices found**
  - Ensure device is online and accessible in Alexa app
  - Verify device is registered to the same Amazon account
  - Check device appears in https://alexa.amazon.co.uk/spa/index.html

- **Device ID format error**
  - Device ID should be UUID format (e.g., `e1234567-89ab-cdef-0123-456789abcdef`)
  - Serial should be in format `GAJ...` (15 characters)

### Data Retrieval Issues
- **No readings returned**
  - Check device has latest firmware in Alexa app
  - Verify sensor capabilities (all AQMs have temp/humidity, some have PM2.5/VOC/CO)
  - Review logs with `--log-level DEBUG` for API response details

- **Validation errors**
  - Temperature out of range: Check device is functioning properly
  - Humidity > 100%: Sensor may need calibration
  - Negative values: May indicate sensor malfunction

### Database Issues
- **Duplicate timestamp error**
  - Database has UNIQUE constraint on (device_id, timestamp)
  - This is expected behavior - prevents duplicate readings
  - Readings are rounded to nearest second

- **Missing columns (co_ppm, iaq_score)**
  - Run database migration script
  - Schema will auto-migrate on first insert if columns missing

### Network/API Issues
- **Timeout errors**
  - Increase `timeout_seconds` in config (default: 30)
  - Check network connectivity to Amazon services
  - Try increasing `max_timeout` for slower connections

- **Rate limiting**
  - Amazon may throttle requests if polling too frequently
  - Recommended: 5-minute intervals (300 seconds)
  - Exponential backoff is built-in (1s, 2s, 4s delays)

---

Ready for production use with robust error handling and validation.

````
