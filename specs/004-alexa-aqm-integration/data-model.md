# Data Model: Alexa AQM Integration

## Entities

### User
- **Attributes**:
  - amazon_credentials (stored securely)
  - selected_device_id

### Device
- **Attributes**:
  - device_id (composite: `alexa:<device_id>`)
  - device_type ("Amazon Air Quality Monitor")
  - accessibility_status
  - sensor_capabilities (temperature, humidity)

### Authentication Credentials
- **Attributes**:
  - token
  - expiration_time
  - validity

### Air Quality Reading
- **Attributes**:
  - device_id (composite)
  - sensor_type (temperature, humidity)
  - value
  - unit (°C, %)
  - timestamp (ISO 8601)
  - location (room/zone)

### Sensor
- **Attributes**:
  - sensor_type (temperature, humidity)
  - current_value
  - unit

## Relationships
- User owns Device(s)
- Device has Sensor(s)
- Device produces Air Quality Reading(s)
- Authentication Credentials linked to User

## Validation Rules
- Temperature: 0°C to 40°C (indoor)
- Humidity: 0% to 100%
- Required fields: device_id, sensor_type, value, unit, timestamp
- Duplicate timestamp detection per device

## State Transitions
- Authentication: unauthenticated → authenticated → expired/invalid
- Device: inaccessible → accessible → selected
- Data retrieval: pending → success → error

---

All entities and rules mapped for Phase 1 contracts and implementation.
