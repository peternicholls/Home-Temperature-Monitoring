-- Database Schema for Home Temperature Monitoring
-- Sprint 0: Project Foundation
-- Created: 2025-11-18
-- Main readings table
CREATE TABLE IF NOT EXISTS readings (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Required fields
    timestamp DATETIME NOT NULL,
    device_id TEXT NOT NULL,
    temperature_celsius REAL NOT NULL,
    location TEXT NOT NULL,
    device_type TEXT NOT NULL CHECK(
        device_type IN ('hue_sensor', 'nest_thermostat', 'weather_api')
    ),
    -- Optional metadata fields
    humidity_percent REAL CHECK(
        humidity_percent IS NULL
        OR (
            humidity_percent >= 0
            AND humidity_percent <= 100
        )
    ),
    battery_level INTEGER CHECK(
        battery_level IS NULL
        OR (
            battery_level >= 0
            AND battery_level <= 100
        )
    ),
    signal_strength INTEGER CHECK(
        signal_strength IS NULL
        OR (
            signal_strength >= 0
            AND signal_strength <= 100
        )
    ),
    thermostat_mode TEXT CHECK(
        thermostat_mode IS NULL
        OR thermostat_mode IN ('heating', 'cooling', 'off', 'away')
    ),
    thermostat_state TEXT CHECK(
        thermostat_state IS NULL
        OR thermostat_state IN ('active', 'idle')
    ),
    day_night TEXT CHECK(
        day_night IS NULL
        OR day_night IN ('day', 'night')
    ),
    weather_conditions TEXT,
    -- Pipe-separated: sunny|cloudy|raining|snowing|windy
    raw_response TEXT,
    -- Full JSON API response for debugging
    -- Audit field
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    UNIQUE(device_id, timestamp),
    CHECK(
        temperature_celsius >= -40
        AND temperature_celsius <= 50
    )
);
-- Indexes for efficient time-series queries
CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_readings_device_id ON readings(device_id);
CREATE INDEX IF NOT EXISTS idx_readings_device_timestamp ON readings(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_readings_location ON readings(location);
CREATE INDEX IF NOT EXISTS idx_readings_device_type ON readings(device_type);
-- Schema version tracking (for future migrations)
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);
-- Insert initial schema version
INSERT
    OR IGNORE INTO schema_version (version, description)
VALUES (
        1,
        'Initial schema: readings table with temperature data and metadata'
    );