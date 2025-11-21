# SQLite schema definition
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    device_id TEXT NOT NULL,
    temperature_celsius REAL NOT NULL,
    location TEXT NOT NULL,
    device_type TEXT NOT NULL CHECK(device_type IN ('hue_sensor', 'nest_thermostat', 'weather_api', 'alexa_aqm', 'amazon_aqm')),
    is_anomalous BOOLEAN DEFAULT 0,
    humidity_percent REAL CHECK(humidity_percent IS NULL OR (humidity_percent >= 0 AND humidity_percent <= 100)),
    pm25_ugm3 REAL CHECK(pm25_ugm3 IS NULL OR pm25_ugm3 >= 0),
    voc_ppb REAL CHECK(voc_ppb IS NULL OR voc_ppb >= 0),
    co_ppm REAL CHECK(co_ppm IS NULL OR co_ppm >= 0),
    co2_ppm REAL CHECK(co2_ppm IS NULL OR co2_ppm >= 0),
    iaq_score REAL CHECK(iaq_score IS NULL OR (iaq_score >= 0 AND iaq_score <= 100)),
    battery_level INTEGER CHECK(battery_level IS NULL OR (battery_level >= 0 AND battery_level <= 100)),
    signal_strength INTEGER CHECK(signal_strength IS NULL OR (signal_strength >= 0 AND signal_strength <= 100)),
    thermostat_mode TEXT CHECK(thermostat_mode IS NULL OR thermostat_mode IN ('heating', 'cooling', 'off', 'away')),
    thermostat_state TEXT CHECK(thermostat_state IS NULL OR thermostat_state IN ('active', 'idle')),
    day_night TEXT CHECK(day_night IS NULL OR day_night IN ('day', 'night')),
    weather_conditions TEXT,
    raw_response TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_id, timestamp),
    CHECK(temperature_celsius >= -40 AND temperature_celsius <= 50)
);
CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_readings_device_id ON readings(device_id);
CREATE INDEX IF NOT EXISTS idx_readings_device_timestamp ON readings(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_readings_location ON readings(location);
CREATE INDEX IF NOT EXISTS idx_readings_device_type ON readings(device_type);
CREATE INDEX IF NOT EXISTS idx_readings_anomalous ON readings(is_anomalous) WHERE is_anomalous = 1;
"""
