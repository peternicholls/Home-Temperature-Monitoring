import pytest
import sqlite3
import tempfile
import os
from contextlib import closing


# Mock database helper
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
    
    # Create readings table with device_name and location columns
    cursor.execute("""
        CREATE TABLE readings (
            reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_id TEXT NOT NULL,
            device_name TEXT,
            location TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            temperature REAL,
            humidity REAL,
            pm25 REAL
        )
    """)
    
    conn.commit()
    conn.close()
    
    return db_path


# Mock function: Hue collector discovers and registers a sensor
def hue_collector_process_sensor(db_path, sensor_data):
    """
    Simulates Hue collector processing a sensor:
    1. Check if device exists in registry
    2. Register if new
    3. Update last_seen if existing
    4. Return device info for storing reading
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    unique_id = sensor_data['unique_id']
    device_type = 'hue_sensor'
    model_info = sensor_data.get('model', 'ZLLTemperature')
    
    # Extract location from sensor name
    sensor_name = sensor_data.get('name', '')
    location = sensor_name.replace('sensor', '').replace('temperature', '').strip().title()
    
    with closing(conn):
        # Check if device exists
        cursor.execute("SELECT device_name, location FROM device_registry WHERE unique_id = ?", (unique_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update last_seen
            cursor.execute("""
                UPDATE device_registry 
                SET last_seen = CURRENT_TIMESTAMP
                WHERE unique_id = ?
            """, (unique_id,))
            device_name, device_location = existing
        else:
            # Register new device with auto-detected location
            device_name = sensor_name  # Use sensor name as default device name
            cursor.execute("""
                INSERT INTO device_registry (device_type, device_name, location, unique_id, model_info)
                VALUES (?, ?, ?, ?, ?)
            """, (device_type, device_name, location, unique_id, model_info))
            device_location = location
        
        conn.commit()
        return {'device_name': device_name, 'location': device_location}


# Mock function: Amazon collector discovers and registers a device
def amazon_collector_process_device(db_path, device_data):
    """
    Simulates Amazon AQM collector processing a device:
    1. Check if device exists in registry
    2. Register if new
    3. Update last_seen if existing
    4. Return device info for storing reading
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    unique_id = device_data['unique_id']
    device_type = 'amazon_aqm'
    model_info = device_data.get('model', 'A3VRME03NAXFUB')
    
    # Extract location from displayName
    display_name = device_data.get('displayName', '')
    location = display_name.replace('Air Quality Monitor', '').replace('AQM', '').strip().title()
    
    with closing(conn):
        # Check if device exists
        cursor.execute("SELECT device_name, location FROM device_registry WHERE unique_id = ?", (unique_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update last_seen
            cursor.execute("""
                UPDATE device_registry 
                SET last_seen = CURRENT_TIMESTAMP
                WHERE unique_id = ?
            """, (unique_id,))
            device_name, device_location = existing
        else:
            # Register new device with auto-detected location
            device_name = display_name  # Use displayName as default device name
            cursor.execute("""
                INSERT INTO device_registry (device_type, device_name, location, unique_id, model_info)
                VALUES (?, ?, ?, ?, ?)
            """, (device_type, device_name, location, unique_id, model_info))
            device_location = location
        
        conn.commit()
        return {'device_name': device_name, 'location': device_location}


# Mock function: Store reading with device info from registry
def store_reading_from_collector(db_path, unique_id, temperature=None, humidity=None, pm25=None):
    """Store a reading with device_name and location from registry."""
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
        
        # Store reading with all device context
        cursor.execute("""
            INSERT INTO readings (unique_id, device_name, location, temperature, humidity, pm25)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (unique_id, device_name, location, temperature, humidity, pm25))
        
        conn.commit()
        return True


# T143: Test Hue collector uses device registry
def test_hue_collector_uses_device_registry():
    """Should verify that the Hue collector registers and uses device names from the registry."""
    db_path = create_test_db_file()
    
    try:
        # Simulate Hue collector discovering a sensor
        sensor_data = {
            'unique_id': 'hue-sensor-001',
            'name': 'Living Room sensor',
            'model': 'ZLLTemperature'
        }
        
        # Process sensor (should auto-register)
        device_info = hue_collector_process_sensor(db_path, sensor_data)
        
        assert device_info is not None
        assert device_info['device_name'] == 'Living Room sensor'
        assert device_info['location'] == 'Living Room'
        
        # Verify device in registry
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT device_type, device_name, location, model_info FROM device_registry WHERE unique_id = ?", 
                      ('hue-sensor-001',))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == 'hue_sensor'
        assert result[1] == 'Living Room sensor'
        assert result[2] == 'Living Room'
        assert result[3] == 'ZLLTemperature'
        
        # Process same sensor again (should update last_seen, not create duplicate)
        device_info = hue_collector_process_sensor(db_path, sensor_data)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM device_registry WHERE unique_id = ?", ('hue-sensor-001',))
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 1  # Only one entry
        
    finally:
        os.unlink(db_path)


# T144: Test Amazon collector uses device registry
def test_amazon_collector_uses_device_registry():
    """Should verify that the Amazon collector registers and uses device names from the registry."""
    db_path = create_test_db_file()
    
    try:
        # Simulate Amazon collector discovering a device
        device_data = {
            'unique_id': 'amazon-aqm-001',
            'displayName': 'Bedroom Air Quality Monitor',
            'model': 'A3VRME03NAXFUB'
        }
        
        # Process device (should auto-register)
        device_info = amazon_collector_process_device(db_path, device_data)
        
        assert device_info is not None
        assert device_info['device_name'] == 'Bedroom Air Quality Monitor'
        assert device_info['location'] == 'Bedroom'
        
        # Verify device in registry
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT device_type, device_name, location, model_info FROM device_registry WHERE unique_id = ?", 
                      ('amazon-aqm-001',))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == 'amazon_aqm'
        assert result[1] == 'Bedroom Air Quality Monitor'
        assert result[2] == 'Bedroom'
        assert result[3] == 'A3VRME03NAXFUB'
        
        # Process same device again (should update last_seen, not duplicate)
        device_info = amazon_collector_process_device(db_path, device_data)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM device_registry WHERE unique_id = ?", ('amazon-aqm-001',))
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 1  # Only one entry
        
    finally:
        os.unlink(db_path)


# T145: Test readings include device name and location
def test_readings_include_device_name_and_location():
    """Should verify that readings include device name and location from the registry."""
    db_path = create_test_db_file()
    
    try:
        # Register a Hue sensor
        hue_sensor = {
            'unique_id': 'hue-001',
            'name': 'Kitchen sensor',
            'model': 'ZLLTemperature'
        }
        hue_collector_process_sensor(db_path, hue_sensor)
        
        # Register an Amazon device
        amazon_device = {
            'unique_id': 'amazon-001',
            'displayName': 'Office Air Quality Monitor',
            'model': 'A3VRME03NAXFUB'
        }
        amazon_collector_process_device(db_path, amazon_device)
        
        # Store readings
        result = store_reading_from_collector(db_path, 'hue-001', temperature=21.5)
        assert result is True
        
        result = store_reading_from_collector(db_path, 'amazon-001', temperature=22.0, humidity=45.0, pm25=8.0)
        assert result is True
        
        # Verify Hue reading includes device context
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT device_name, location, temperature FROM readings 
            WHERE unique_id = ?
        """, ('hue-001',))
        hue_reading = cursor.fetchone()
        
        assert hue_reading is not None
        assert hue_reading[0] == 'Kitchen sensor'
        assert hue_reading[1] == 'Kitchen'
        assert hue_reading[2] == 21.5
        
        # Verify Amazon reading includes device context
        cursor.execute("""
            SELECT device_name, location, temperature, humidity, pm25 FROM readings 
            WHERE unique_id = ?
        """, ('amazon-001',))
        amazon_reading = cursor.fetchone()
        
        assert amazon_reading is not None
        assert amazon_reading[0] == 'Office Air Quality Monitor'
        assert amazon_reading[1] == 'Office'
        assert amazon_reading[2] == 22.0
        assert amazon_reading[3] == 45.0
        assert amazon_reading[4] == 8.0
        
        conn.close()
        
    finally:
        os.unlink(db_path)


# T146: Test unknown device auto-registered
def test_unknown_device_auto_registered():
    """Should verify that unknown devices are automatically registered in the registry."""
    db_path = create_test_db_file()
    
    try:
        # Verify registry is empty
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM device_registry")
        initial_count = cursor.fetchone()[0]
        conn.close()
        assert initial_count == 0
        
        # Collector encounters unknown Hue sensor
        new_hue_sensor = {
            'unique_id': 'hue-new-sensor',
            'name': 'Garage sensor',
            'model': 'ZLLTemperature'
        }
        device_info = hue_collector_process_sensor(db_path, new_hue_sensor)
        
        # Verify it was auto-registered
        assert device_info is not None
        assert device_info['device_name'] == 'Garage sensor'
        assert device_info['location'] == 'Garage'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM device_registry")
        count_after_hue = cursor.fetchone()[0]
        conn.close()
        assert count_after_hue == 1
        
        # Collector encounters unknown Amazon device
        new_amazon_device = {
            'unique_id': 'amazon-new-device',
            'displayName': 'Basement Air Quality Monitor',
            'model': 'A3VRME03NAXFUB'
        }
        device_info = amazon_collector_process_device(db_path, new_amazon_device)
        
        # Verify it was auto-registered
        assert device_info is not None
        assert device_info['device_name'] == 'Basement Air Quality Monitor'
        assert device_info['location'] == 'Basement'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM device_registry")
        final_count = cursor.fetchone()[0]
        conn.close()
        assert final_count == 2
        
        # Verify both devices can store readings immediately
        result = store_reading_from_collector(db_path, 'hue-new-sensor', temperature=18.0)
        assert result is True
        
        result = store_reading_from_collector(db_path, 'amazon-new-device', temperature=19.5, humidity=50.0)
        assert result is True
        
        # Verify readings have device context
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM readings WHERE device_name IS NOT NULL AND location IS NOT NULL")
        readings_with_context = cursor.fetchone()[0]
        conn.close()
        assert readings_with_context == 2
        
    finally:
        os.unlink(db_path)
