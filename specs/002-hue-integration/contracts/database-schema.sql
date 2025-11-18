-- Database schema for Philips Hue temperature readings
-- Feature: 002-hue-integration
-- Date: 2025-11-18
--
-- NOTE: This schema is auto-created by source/storage/manager.py if the table
--       doesn't exist. This file serves as documentation and can be used for
--       manual database initialization if needed.
--
-- Main temperature readings table
CREATE TABLE IF NOT EXISTS temperature_readings (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Required fields (per constitution)
    timestamp TEXT NOT NULL,
    -- ISO 8601 with timezone (e.g., "2025-11-18T14:30:00+00:00")
    device_id TEXT NOT NULL,
    -- Composite format: hue:<sensor_unique_id>
    temperature_celsius REAL NOT NULL,
    -- Standard Celsius (converted from 0.01°C units)
    location TEXT NOT NULL,
    -- Room/zone name (from config or Hue metadata)
    device_type TEXT NOT NULL,
    -- Fixed: 'hue_sensor' for this feature
    -- Validation metadata
    is_anomalous BOOLEAN DEFAULT 0,
    -- Flag for readings outside 0-40°C range
    -- Optional metadata (availability depends on sensor)
    battery_level INTEGER,
    -- Battery percentage (0-100)
    signal_strength INTEGER,
    -- Connectivity: 0=unreachable, 1=reachable
    raw_api_response TEXT,
    -- Full API response JSON (for debugging)
    -- Audit timestamp
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    UNIQUE(device_id, timestamp),
    -- Prevent duplicate readings
    CHECK(temperature_celsius IS NOT NULL),
    CHECK(
        battery_level IS NULL
        OR (
            battery_level >= 0
            AND battery_level <= 100
        )
    )
);
-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_device_timestamp ON temperature_readings(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_timestamp ON temperature_readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_anomalous ON temperature_readings(is_anomalous)
WHERE is_anomalous = 1;
-- Sample queries for validation
-- Query 1: Get last 24 hours of readings for a specific sensor
-- SELECT timestamp, temperature_celsius, location, is_anomalous
-- FROM temperature_readings
-- WHERE device_id = 'hue:00:17:88:01:02:03:04:05-02-0402'
--   AND timestamp >= datetime('now', '-1 day')
-- ORDER BY timestamp DESC;
-- Query 2: Get all readings in a time range across all Hue sensors
-- SELECT timestamp, device_id, location, temperature_celsius
-- FROM temperature_readings
-- WHERE device_type = 'hue_sensor'
--   AND timestamp BETWEEN '2025-11-18T00:00:00+00:00' AND '2025-11-18T23:59:59+00:00'
-- ORDER BY timestamp ASC;
-- Query 3: Find anomalous readings
-- SELECT timestamp, device_id, location, temperature_celsius, 
--        CASE WHEN temperature_celsius < 0 THEN 'Below minimum'
--             WHEN temperature_celsius > 40 THEN 'Above maximum'
--        END as anomaly_reason
-- FROM temperature_readings
-- WHERE is_anomalous = 1
-- ORDER BY timestamp DESC;
-- Query 4: Check for duplicate timestamps (should return empty)
-- SELECT device_id, timestamp, COUNT(*) as duplicate_count
-- FROM temperature_readings
-- GROUP BY device_id, timestamp
-- HAVING COUNT(*) > 1;
-- Query 5: Get collection success rate per device (last 7 days)
-- Expected: 288 readings/day * 7 days = 2016 readings per sensor
-- SELECT device_id, 
--        location,
--        COUNT(*) as readings_count,
--        MIN(timestamp) as first_reading,
--        MAX(timestamp) as last_reading,
--        ROUND(COUNT(*) * 100.0 / 2016, 2) as success_rate_percent
-- FROM temperature_readings
-- WHERE timestamp >= datetime('now', '-7 days')
-- GROUP BY device_id
-- ORDER BY success_rate_percent DESC;