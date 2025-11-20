# Amazon Alexa Air Quality Monitor - Real World Usage Guide

## Overview

This implementation uses **cookie-based authentication** with **direct GraphQL API calls** to Amazon's Alexa services. It does NOT require alexapy or Home Assistant - it works directly with Amazon's APIs using the same approach that Home Assistant's Alexa Media Player integration uses internally.

## Prerequisites

1. **Amazon Smart Air Quality Monitor** device registered to your Amazon account
2. **Python 3.10+** with playwright library
3. **Valid Amazon account** with access to the device

## Setup Instructions

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium  # Install browser for cookie capture
```

### Step 2: Capture Amazon Cookies

Run the cookie capture tool:

```bash
python -m source.collectors.amazon_auth
```

This will:
1. Open a Chromium browser window
2. Navigate to Amazon login page
3. Wait for you to log in manually
4. Capture authentication cookies
5. Save cookies to `config/secrets.yaml`

**Important**: Log in with the SAME Amazon account that has your Air Quality Monitor registered.

### Step 3: Verify Cookies in secrets.yaml

Check that `config/secrets.yaml` contains:

```yaml
amazon_aqm:
  cookies:
    at-main: "your-at-main-cookie"
    csrf: "your-csrf-token"
    lc-main: "your-lc-main-cookie"
    sess-at-main: "your-sess-at-main-cookie"
    session-id: "your-session-id"
    session-id-time: "your-session-id-time"
    session-token: "your-session-token"
    ubid-main: "your-ubid-main"
    x-main: "your-x-main"
```

### Step 4: Test Data Collection

Create a test script `test_collection.py`:

```python
import asyncio
import yaml
import logging
from source.collectors.amazon_collector import collect_amazon_aqm_data

logging.basicConfig(level=logging.INFO)

async def main():
    # Load cookies from secrets
    with open('config/secrets.yaml') as f:
        secrets = yaml.safe_load(f)
    
    cookies = secrets['amazon_aqm']['cookies']
    
    # Load configuration
    with open('config/config.yaml') as f:
        config = yaml.safe_load(f)
    
    # Collect data
    result = await collect_amazon_aqm_data(cookies, config)
    
    if result:
        print("✅ Collection successful!")
        print(f"Device: {result['device_name']}")
        print(f"Device ID: {result['device_id']}")
        print("Readings:")
        for key, value in result['readings'].items():
            if key != 'timestamp':
                print(f"  {key}: {value}")
    else:
        print("❌ Collection failed - check logs")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python test_collection.py
```

Expected output:
```
✅ Collection successful!
Device: Living Room
Device ID: alexa:G000AA1234567890
Readings:
  temperature_celsius: 22.5
  humidity_percent: 45.0
  pm25_ugm3: 12.5
  voc_ppb: 150
  co2_ppm: 650
```

## How It Works

### Authentication Flow

1. **Cookie Capture** (one-time setup):
   - Playwright opens browser
   - User logs into Amazon manually
   - Tool captures session cookies
   - Cookies stored in secrets.yaml

2. **API Calls** (every collection):
   - Uses stored cookies for authentication
   - No email/password needed after initial setup
   - Cookies include CSRF token for API requests

### Data Collection Flow

1. **Device Discovery** (GraphQL):
   ```
   POST https://alexa.amazon.com/nexus/v1/graphql
   Query: CustomerSmartHome endpoint list
   Response: All smart home devices including Air Quality Monitors
   ```

2. **Data Retrieval** (Phoenix API):
   ```
   GET https://alexa.amazon.com/api/phoenix/state
   Response: Current state of all entities (temp, humidity, PM2.5, VOC, CO2)
   ```

3. **Data Validation**:
   - Temperature: 0-40°C
   - Humidity: 0-100%
   - PM2.5, VOC, CO2: non-negative values

4. **Database Storage**:
   - Composite device_id: `alexa:G000AA1234567890`
   - All air quality readings saved to SQLite
   - Timestamps, device metadata included

## Troubleshooting

### No Devices Found

**Problem**: GraphQL returns empty device list

**Solutions**:
1. Verify device is registered in Alexa app (alexa.amazon.com)
2. Check you're logged into correct Amazon account
3. Recapture cookies if they expired
4. Check device shows as "online" in Alexa app

### Authentication Failed

**Problem**: API returns 401/403 errors

**Solutions**:
1. Cookies may have expired - recapture them
2. CSRF token might be missing - ensure `csrf` cookie is captured
3. Try logging out and back in to Amazon
4. Clear browser cookies and recapture

### No Air Quality Data

**Problem**: Device found but no readings returned

**Solutions**:
1. Check device is actually online and collecting data
2. View data in Alexa app first to confirm it's working
3. Check phoenix API response for entity_id
4. Verify capabilities list includes air quality sensors

## Cookie Expiration

Amazon cookies typically expire after **30-90 days**. When cookies expire:

1. You'll see authentication errors in logs
2. Re-run the cookie capture tool:
   ```bash
   python -m source.collectors.amazon_auth
   ```
3. Log in again when browser opens
4. New cookies will be saved automatically

## Security Notes

1. **Never commit secrets.yaml** to version control
2. Cookies provide full access to your Amazon account
3. Store secrets.yaml with restricted permissions (chmod 600)
4. Cookies are equivalent to your password - protect them carefully
5. Use different Amazon account for testing if possible

## Comparison to alexapy Approach

| Feature | Cookie-based (This) | alexapy Library |
|---------|-------------------|-----------------|
| **Dependencies** | playwright, requests | alexapy |
| **Setup** | One-time browser login | Email/password in code |
| **Authentication** | Cookie-based | Email/password each time |
| **API Calls** | Direct HTTP/GraphQL | Through alexapy wrapper |
| **Maintenance** | Recapture cookies when expired | Update library versions |
| **Transparency** | See exact API calls | Abstract library layer |
| **Home Assistant Compatible** | Same approach as HA | Uses alexapy |

## Production Usage

For production deployment:

1. **Automate cookie renewal**:
   - Set up cron job to check cookie expiration
   - Alert when cookies need renewal
   - Consider using headless browser automation

2. **Monitor collection**:
   - Log all API responses
   - Alert on consecutive failures
   - Track cookie expiration dates

3. **Error handling**:
   - Retry logic already implemented (5 attempts)
   - Exponential backoff prevents API rate limiting
   - Validation catches bad data before storage

4. **Database management**:
   - Regular backups
   - Check for duplicate timestamps
   - Monitor storage growth

## API Endpoints Reference

### GraphQL Endpoint
```
URL: https://alexa.amazon.com/nexus/v1/graphql
Method: POST
Headers:
  - csrf: <csrf_token_from_cookies>
  - Referer: https://alexa.amazon.com/spa/index.html
  - Cookie: <all_captured_cookies>
Body:
  {
    "query": "query CustomerSmartHome { ... }"
  }
```

### Phoenix State API
```
URL: https://alexa.amazon.com/api/phoenix/state
Method: GET
Headers: Same as GraphQL
Response: JSON with entity states
```

## Next Steps

1. **Schedule regular collection**:
   ```bash
   # Add to crontab for hourly collection
   0 * * * * cd /path/to/project && python test_collection.py
   ```

2. **Set up monitoring**:
   - Track collection success rate
   - Alert on data quality issues
   - Monitor cookie expiration

3. **Expand functionality**:
   - Support multiple devices
   - Add historical data analysis
   - Create visualization dashboard

## Support

If you encounter issues:

1. Check logs for error details
2. Verify device works in Alexa app
3. Try recapturing cookies
4. Check Amazon service status
5. Review firewall/proxy settings
