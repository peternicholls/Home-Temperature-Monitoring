import pytest
import sqlite3
import tempfile
import os
from contextlib import closing


# Mock database helper for creating test SQLite file
def create_test_db_file():
    """Create a temporary SQLite database file with device_registry and readings schemas."""
    temp_db = tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False)
    db_path = temp_db.name
    temp_db.close()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create device_registry table
    cursor.execute("""
        CREATE TABLE device_registry (
            device_id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_type TEXT NOT NULL,
            device_name TEXT,
            location TEXT,
            unique_id TEXT UNIQUE NOT NULL,
            model_info TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Create readings table
    cursor.execute("""
        CREATE TABLE readings (
            reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_id TEXT NOT NULL,
            device_name TEXT,
            location TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            temperature REAL
        )
    """)
    
    conn.commit()
    conn.close()
    
    return db_path


# Mock function to extract location from Hue sensor payload
def extract_location_from_hue_sensor(sensor_payload):
    """Extract location from a Hue sensor's name field.
    
    Hue sensors typically have names like 'Living Room sensor' or 'Bedroom temperature'.
    This extracts the location prefix before common keywords.
    """
    name = sensor_payload.get('name', '')
    
    # Common sensor keywords to remove
    keywords = ['sensor', 'temperature', 'motion', 'hue']
    
    location = name.lower()
    for keyword in keywords:
        location = location.replace(keyword, '')
    
    # Clean up and capitalize
    location = location.strip().title()
    
    return location if location else None


# Mock function to extract location from Amazon AQM device payload
def extract_location_from_amazon_aqm_device(device_payload):
    """Extract location from Amazon AQM device's displayName field.
    
    Amazon devices have displayNames like 'Master Bedroom Air Quality Monitor'.
    Extract the location prefix before 'Air Quality Monitor'.
    """
    display_name = device_payload.get('displayName', '')
    
    # Remove common Amazon AQM suffixes
    suffixes = ['air quality monitor', 'aqm', 'monitor']
    
    location = display_name.lower()
    for suffix in suffixes:
        location = location.replace(suffix, '')
    
    # Clean up and capitalize
    location = location.strip().title()
    
    return location if location else None


# Mock function to store location in device registry
def store_location_in_device_registry(db_path, unique_id, location):
    """Store or update location for a device in the registry."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with closing(conn):
        cursor.execute("""
            UPDATE device_registry 
            SET location = ?, last_seen = CURRENT_TIMESTAMP
            WHERE unique_id = ?
        """, (location, unique_id))
        
        conn.commit()
        return cursor.rowcount > 0


# Mock function to get device with location
def get_device_with_location(db_path, unique_id):
    """Retrieve device with location from registry."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with closing(conn):
        cursor.execute("""
            SELECT device_name, location FROM device_registry WHERE unique_id = ?
        """, (unique_id,))
        
        result = cursor.fetchone()
        return {'device_name': result[0], 'location': result[1]} if result else None


# Mock function to store reading with location
def store_reading_with_location(db_path, unique_id, temperature):
    """Store a reading with device name and location from registry."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with closing(conn):
        # Get device info from registry
        cursor.execute("""
            SELECT device_name, location FROM device_registry WHERE unique_id = ?
        """, (unique_id,))
        
        device_info = cursor.fetchone()
        if not device_info:
            return False
        
        device_name, location = device_info
        
        # Store reading with location
        cursor.execute("""
            INSERT INTO readings (unique_id, device_name, location, temperature)
            VALUES (?, ?, ?, ?)
        """, (unique_id, device_name, location, temperature))
        
        conn.commit()
        return True


# Mock function to override location via config
def apply_location_override(db_path, unique_id, config_overrides):
    """Apply location override from config if present."""
    override_location = config_overrides.get(unique_id)
    
    if override_location:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        with closing(conn):
            cursor.execute("""
                UPDATE device_registry 
                SET location = ?
                WHERE unique_id = ?
            """, (override_location, unique_id))
            
            conn.commit()
            return True
    
    return False


# T138: Test extract location from Hue sensor
def test_extract_location_from_hue_sensor():
    """Should extract location info from a Hue sensor payload."""
    # Test typical Hue sensor name format
    sensor_payload = {'name': 'Living Room sensor', 'type': 'ZLLTemperature'}
    location = extract_location_from_hue_sensor(sensor_payload)
    assert location == 'Living Room'
    
    # Test alternative format
    sensor_payload = {'name': 'Bedroom Temperature', 'type': 'ZLLTemperature'}
    location = extract_location_from_hue_sensor(sensor_payload)
    assert location == 'Bedroom'
    
    # Test with motion sensor
    sensor_payload = {'name': 'Kitchen Motion Sensor', 'type': 'ZLLPresence'}
    location = extract_location_from_hue_sensor(sensor_payload)
    assert location == 'Kitchen'
    
    # Test empty name
    sensor_payload = {'name': '', 'type': 'ZLLTemperature'}
    location = extract_location_from_hue_sensor(sensor_payload)
    assert location is None


# T139: Test extract location from Amazon AQM device
def test_extract_location_from_amazon_aqm_device():
    """Should extract location info from an Amazon AQM device payload."""
    # Test typical Amazon AQM displayName format
    device_payload = {'displayName': 'Master Bedroom Air Quality Monitor', 'deviceType': 'A3VRME03NAXFUB'}
    location = extract_location_from_amazon_aqm_device(device_payload)
    assert location == 'Master Bedroom'
    
    # Test short format
    device_payload = {'displayName': 'Kitchen AQM', 'deviceType': 'A3VRME03NAXFUB'}
    location = extract_location_from_amazon_aqm_device(device_payload)
    assert location == 'Kitchen'
    
    # Test with 'Monitor' only
    device_payload = {'displayName': 'Office Monitor', 'deviceType': 'A3VRME03NAXFUB'}
    location = extract_location_from_amazon_aqm_device(device_payload)
    assert location == 'Office'
    
    # Test empty displayName
    device_payload = {'displayName': '', 'deviceType': 'A3VRME03NAXFUB'}
    location = extract_location_from_amazon_aqm_device(device_payload)
    assert location is None


# T140: Test store location in device registry
def test_store_location_in_device_registry():
    """Should store extracted location in the device registry."""
    db_path = create_test_db_file()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert a device without location
        cursor.execute("""
            INSERT INTO device_registry (device_type, device_name, unique_id, model_info)
            VALUES (?, ?, ?, ?)
        """, ('hue_sensor', 'Living Room Temp', 'hue-001', 'ZLLTemperature'))
        conn.commit()
        conn.close()
        
        # Store location
        result = store_location_in_device_registry(db_path, 'hue-001', 'Living Room')
        assert result is True
        
        # Verify location stored
        device = get_device_with_location(db_path, 'hue-001')
        assert device is not None
        assert device['location'] == 'Living Room'
        assert device['device_name'] == 'Living Room Temp'
        
        # Update location
        result = store_location_in_device_registry(db_path, 'hue-001', 'Family Room')
        assert result is True
        
        device = get_device_with_location(db_path, 'hue-001')
        assert device['location'] == 'Family Room'
        
    finally:
        os.unlink(db_path)


# T141: Test location propagation to readings
def test_location_propagation_to_readings():
    """Should ensure readings include the correct location from the registry."""
    db_path = create_test_db_file()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert device with location
        cursor.execute("""
            INSERT INTO device_registry (device_type, device_name, location, unique_id, model_info)
            VALUES (?, ?, ?, ?, ?)
        """, ('hue_sensor', 'Bedroom Sensor', 'Bedroom', 'hue-002', 'ZLLTemperature'))
        conn.commit()
        conn.close()
        
        # Store reading (should propagate location)
        result = store_reading_with_location(db_path, 'hue-002', 22.5)
        assert result is True
        
        # Verify reading has location
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT device_name, location, temperature FROM readings WHERE unique_id = ?", ('hue-002',))
        reading = cursor.fetchone()
        conn.close()
        
        assert reading is not None
        assert reading[0] == 'Bedroom Sensor'  # device_name
        assert reading[1] == 'Bedroom'  # location
        assert reading[2] == 22.5  # temperature
        
        # Store another reading
        result = store_reading_with_location(db_path, 'hue-002', 23.1)
        assert result is True
        
        # Verify both readings have location
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM readings WHERE unique_id = ? AND location = ?", ('hue-002', 'Bedroom'))
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 2
        
    finally:
        os.unlink(db_path)


# T142: Test location override via config
def test_location_override_via_config():
    """Should override detected location with config value if present."""
    db_path = create_test_db_file()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert device with auto-detected location
        cursor.execute("""
            INSERT INTO device_registry (device_type, device_name, location, unique_id, model_info)
            VALUES (?, ?, ?, ?, ?)
        """, ('hue_sensor', 'Office Sensor', 'Office', 'hue-003', 'ZLLTemperature'))
        conn.commit()
        conn.close()
        
        # Verify initial location
        device = get_device_with_location(db_path, 'hue-003')
        assert device['location'] == 'Office'
        
        # Apply config override
        config_overrides = {
            'hue-003': 'Home Office'  # Override with more specific location
        }
        result = apply_location_override(db_path, 'hue-003', config_overrides)
        assert result is True
        
        # Verify location updated
        device = get_device_with_location(db_path, 'hue-003')
        assert device['location'] == 'Home Office'
        
        # Test no override (device not in config)
        result = apply_location_override(db_path, 'hue-003', {})
        assert result is False
        
        # Verify location unchanged
        device = get_device_with_location(db_path, 'hue-003')
        assert device['location'] == 'Home Office'
        
    finally:
        os.unlink(db_path)
