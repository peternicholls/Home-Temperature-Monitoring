# Critical Discovery: Amazon Uses GraphQL!

## Root Cause Found

The issue was that we were calling the wrong endpoint. Amazon's Alexa API uses **GraphQL**, not REST.

### Wrong Approach (What We Were Doing)
```python
# ❌ This returns HTTP 299
url = "https://alexa.amazon.com/api/phoenix"
response = session.get(url)
```

### Correct Approach (What alexapy Does)
```python
# ✅ This works!
url = "https://alexa.amazon.com/nexus/v1/graphql"
query = """
query CustomerSmartHome {
    endpoints(
      endpointsQueryParams: { paginationParams: { disablePagination: true } }
    ) {
        items {
            legacyAppliance {
                applianceId
                applianceTypes
                friendlyName
                friendlyDescription
                capabilities
                entityId
                alexaDeviceIdentifierList
            }
        }
    }
}
"""
response = session.post(url, json={"query": query})
```

## Additional Requirements

### 1. CSRF Token
The CSRF token must be extracted from cookies and added to headers:
```python
# Extract from cookies
csrf_token = cookies.get('csrf')

# Add to headers
headers['csrf'] = csrf_token
```

### 2. Referer Header
```python
headers['Referer'] = 'https://alexa.amazon.com/spa/index.html'
```

## How alexapy Works

1. **Login** → Gets cookies (including CSRF token)
2. **Extract CSRF** → From `csrf` cookie
3. **GraphQL Query** → POST to `/nexus/v1/graphql` with:
   - CSRF token in headers
   - Cookies in request
   - GraphQL query in JSON body
4. **Parse Response** → Extract `data.endpoints.items[].legacyAppliance`

## Why HTTP 299?

HTTP 299 was Amazon's way of saying "wrong endpoint" or "deprecated". The `/api/phoenix` REST endpoint may have been deprecated in favor of GraphQL.

## Next Steps

Update our collector to:
1. Use GraphQL endpoint (`/nexus/v1/graphql`)
2. Extract and send CSRF token
3. Send correct headers (Referer)
4. Parse GraphQL response structure

This should solve the authentication issue!
