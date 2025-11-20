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

### 1. Configure Credentials

Add Amazon credentials to `config/secrets.yaml`:

```yaml
amazon:
  email: your-amazon-email@example.com
  password: your-amazon-password
  device_id: alexa:YOUR_DEVICE_SERIAL  # Optional, will be discovered if not set
```

### 2. Optional: Home Assistant Fallback

For fallback support, add Home Assistant credentials:

```yaml
home_assistant:
  url: http://homeassistant.local:8123
  token: YOUR_LONG_LIVED_ACCESS_TOKEN
```

## Authentication

```python
import asyncio
from source.collectors.amazon_auth import authenticate_amazon
from source.config.loader import load_secrets

async def main():
    secrets = load_secrets()
    amazon_config = secrets.get('amazon', {})
    
    # Authenticate
    login = await authenticate_amazon(
        amazon_config['email'],
        amazon_config['password']
    )
    
    if login:
        print("✅ Authentication successful")
    else:
        print("❌ Authentication failed")

asyncio.run(main())
```

## Device Access

```python
import asyncio
from source.collectors.amazon_auth import authenticate_amazon
from source.collectors.amazon_collector import AmazonAQMCollector
from source.config.loader import load_secrets

async def main():
    secrets = load_secrets()
    amazon_config = secrets.get('amazon', {})
    
    # Authenticate
    login = await authenticate_amazon(
        amazon_config['email'],
        amazon_config['password']
    )
    
    if not login:
        print("Authentication failed")
        return
    
    # List devices
    collector = AmazonAQMCollector(login)
    devices = await collector.list_devices()
    
    print(f"Found {len(devices)} air quality monitor(s):")
    for device in devices:
        print(f"  - {device['name']} ({device['device_id']})")
        print(f"    Status: {device['accessibility_status']}")

asyncio.run(main())
```

## Data Retrieval

```python
import asyncio
from source.collectors.amazon_auth import authenticate_amazon
from source.collectors.amazon_collector import collect_amazon_aqm_data
from source.storage.manager import DatabaseManager
from source.config.loader import load_secrets, load_config
from datetime import datetime

async def main():
    secrets = load_secrets()
    config = load_config()
    amazon_config = secrets.get('amazon', {})
    
    # Authenticate
    login = await authenticate_amazon(
        amazon_config['email'],
        amazon_config['password'],
        config
    )
    
    if not login:
        print("Authentication failed")
        return
    
    # Get device ID from config or discover
    device_id = amazon_config.get('device_id')
    if not device_id:
        from source.collectors.amazon_collector import AmazonAQMCollector
        collector = AmazonAQMCollector(login, config)
        devices = await collector.list_devices()
        if devices:
            device_id = devices[0]['device_id']
        else:
            print("No devices found")
            return
    
    # Collect data
    readings = await collect_amazon_aqm_data(login, device_id, config)
    
    if readings:
        print(f"✅ Collected readings:")
        print(f"  Temperature: {readings.get('temperature_celsius')}°C")
        print(f"  Humidity: {readings.get('humidity_percent')}%")
        
        if 'pm25_ugm3' in readings:
            print(f"  PM2.5: {readings['pm25_ugm3']} µg/m³")
        if 'voc_ppb' in readings:
            print(f"  VOC: {readings['voc_ppb']} ppb")
        if 'co2_ppm' in readings:
            print(f"  CO2: {readings['co2_ppm']} ppm")
        
        # Store in database
        db = DatabaseManager(config=config)
        reading_record = {
            'timestamp': readings['timestamp'],
            'device_id': readings['device_id'],
            'temperature_celsius': readings['temperature_celsius'],
            'humidity_percent': readings.get('humidity_percent'),
            'pm25_ugm3': readings.get('pm25_ugm3'),
            'voc_ppb': readings.get('voc_ppb'),
            'co2_ppm': readings.get('co2_ppm'),
            'location': 'unknown',  # Update based on your setup
            'device_type': 'alexa_aqm'
        }
        
        success = db.insert_temperature_reading(reading_record)
        if success:
            print("✅ Readings stored in database")
        else:
            print("⚠️ Duplicate or storage error")
        
        db.close()
    else:
        print("❌ Failed to retrieve readings")

asyncio.run(main())
```

## Home Assistant Fallback

If Amazon authentication fails, use Home Assistant fallback:

```python
from source.collectors.ha_fallback import try_home_assistant_fallback
from source.config.loader import load_secrets

secrets = load_secrets()
ha_config = secrets.get('home_assistant', {})

readings = try_home_assistant_fallback(
    ha_url=ha_config['url'],
    ha_token=ha_config['token'],
    device_name='Air Quality Monitor'  # Optional
)

if readings:
    print(f"✅ Fallback successful: {readings}")
else:
    print("❌ Fallback failed")
```

## Testing

Run unit tests:

```bash
pytest tests/test_amazon_collector.py -v
```

Run with coverage:

```bash
pytest tests/test_amazon_collector.py --cov=source/collectors --cov-report=html
```

## Troubleshooting

### Authentication Issues
- Verify email and password in `config/secrets.yaml`
- Check logs for error details
- Ensure network connectivity to Amazon services
- Try Home Assistant fallback if available

### Device Access Issues
- Ensure device is online and accessible
- Check device ID format (must be `alexa:device_serial`)
- Verify Alexa app shows device as connected

### Data Retrieval Issues
- Check device has latest firmware
- Verify sensor capabilities (not all devices have PM2.5/VOC/CO2)
- Review logs for API errors or timeouts

### Database Issues
- Ensure SQLite database is initialized
- Check for duplicate timestamps (UNIQUE constraint)
- Verify required fields are present

---

Ready for production use with robust error handling and fallback support.

````
