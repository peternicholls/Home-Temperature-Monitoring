import pytest
import sqlite3
from contextlib import closing
import tempfile
import os

# Schema definitions
DEVICE_REGISTRY_SCHEMA = """
CREATE TABLE IF NOT EXISTS device_registry (
    device_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_type TEXT,
    device_name TEXT,
    location TEXT,
    unique_id TEXT UNIQUE,
    model_info TEXT,
    first_seen TEXT,
    last_seen TEXT,
    is_active INTEGER
);
"""

READINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_id TEXT,
    device_name TEXT,
    timestamp TEXT,
    temperature REAL
);
"""

def create_test_db_file():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3')
    tmp.close()
    conn = sqlite3.connect(tmp.name)
    with closing(conn.cursor()) as cur:
        cur.executescript(DEVICE_REGISTRY_SCHEMA + READINGS_SCHEMA)
    return conn, tmp.name

# Mock device manager functions (to be implemented in source/storage/device_manager.py)
def set_device_name(conn, unique_id, device_name, device_type="unknown", location=""):
    """Set device name for a device (insert or update)"""
    with closing(conn.cursor()) as cur:
        # Check if device exists
        cur.execute("SELECT device_id FROM device_registry WHERE unique_id=?", (unique_id,))
        if cur.fetchone():
            # Update existing
            cur.execute("UPDATE device_registry SET device_name=? WHERE unique_id=?", (device_name, unique_id))
        else:
            # Insert new
            cur.execute(
                "INSERT INTO device_registry (unique_id, device_name, device_type, location, first_seen, last_seen, is_active) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), 1)",
                (unique_id, device_name, device_type, location)
            )
        conn.commit()

def amend_device_name(conn, unique_id, new_name, recursive=False):
    """Amend device name, optionally updating historical readings"""
    with closing(conn.cursor()) as cur:
        cur.execute("UPDATE device_registry SET device_name=? WHERE unique_id=?", (new_name, unique_id))
        if recursive:
            cur.execute("UPDATE readings SET device_name=? WHERE unique_id=?", (new_name, unique_id))
        conn.commit()

def get_device_name(conn, unique_id):
    """Get device name from registry"""
    with closing(conn.cursor()) as cur:
        cur.execute("SELECT device_name FROM device_registry WHERE unique_id=?", (unique_id,))
        row = cur.fetchone()
        return row[0] if row else None

def list_devices(conn):
    """List all devices with their names"""
    with closing(conn.cursor()) as cur:
        cur.execute("SELECT unique_id, device_name, device_type, location FROM device_registry ORDER BY unique_id")
        return cur.fetchall()

# T132: Test set device name for new device
def test_set_device_name_new_device():
    conn, db_path = create_test_db_file()
    try:
        set_device_name(conn, "hue-new-123", "Kitchen Sensor", "hue", "Kitchen")
        name = get_device_name(conn, "hue-new-123")
        assert name == "Kitchen Sensor"
    finally:
        conn.close()
        os.unlink(db_path)

# T133: Test set device name for existing device
def test_set_device_name_existing_device():
    conn, db_path = create_test_db_file()
    try:
        # Insert initial device
        set_device_name(conn, "hue-existing-456", "Old Name", "hue", "Bedroom")
        # Update the name
        set_device_name(conn, "hue-existing-456", "Updated Name", "hue", "Bedroom")
        name = get_device_name(conn, "hue-existing-456")
        assert name == "Updated Name"
    finally:
        conn.close()
        os.unlink(db_path)

# T134: Test amend device name without history update
def test_amend_device_name_without_history_update():
    conn, db_path = create_test_db_file()
    try:
        # Setup device and historical reading
        set_device_name(conn, "hue-789", "Original Name", "hue", "Living Room")
        with closing(conn.cursor()) as cur:
            cur.execute("INSERT INTO readings (unique_id, device_name, timestamp, temperature) VALUES (?, ?, ?, ?)",
                       ("hue-789", "Original Name", "2025-11-21T10:00:00", 20.5))
            conn.commit()
        
        # Amend name without recursive update
        amend_device_name(conn, "hue-789", "Amended Name", recursive=False)
        
        # Verify registry updated but reading not updated
        registry_name = get_device_name(conn, "hue-789")
        with closing(conn.cursor()) as cur:
            cur.execute("SELECT device_name FROM readings WHERE unique_id=?", ("hue-789",))
            reading_name = cur.fetchone()[0]
        
        assert registry_name == "Amended Name"
        assert reading_name == "Original Name"  # Should NOT be updated
    finally:
        conn.close()
        os.unlink(db_path)

# T135: Test amend device name with recursive history update
def test_amend_device_name_with_recursive_history_update():
    conn, db_path = create_test_db_file()
    try:
        # Setup device and multiple historical readings
        set_device_name(conn, "hue-abc", "Old Sensor", "hue", "Office")
        with closing(conn.cursor()) as cur:
            cur.execute("INSERT INTO readings (unique_id, device_name, timestamp, temperature) VALUES (?, ?, ?, ?)",
                       ("hue-abc", "Old Sensor", "2025-11-21T09:00:00", 19.5))
            cur.execute("INSERT INTO readings (unique_id, device_name, timestamp, temperature) VALUES (?, ?, ?, ?)",
                       ("hue-abc", "Old Sensor", "2025-11-21T10:00:00", 20.0))
            conn.commit()
        
        # Amend name with recursive update
        amend_device_name(conn, "hue-abc", "New Sensor", recursive=True)
        
        # Verify both registry and all readings updated
        registry_name = get_device_name(conn, "hue-abc")
        with closing(conn.cursor()) as cur:
            cur.execute("SELECT device_name FROM readings WHERE unique_id=?", ("hue-abc",))
            reading_names = [row[0] for row in cur.fetchall()]
        
        assert registry_name == "New Sensor"
        assert all(name == "New Sensor" for name in reading_names)
        assert len(reading_names) == 2  # Both readings updated
    finally:
        conn.close()
        os.unlink(db_path)

# T136: Test get device name from registry
def test_get_device_name_from_registry():
    conn, db_path = create_test_db_file()
    try:
        set_device_name(conn, "hue-xyz", "Test Device", "hue", "Garage")
        name = get_device_name(conn, "hue-xyz")
        assert name == "Test Device"
        
        # Test non-existent device
        name = get_device_name(conn, "nonexistent-id")
        assert name is None
    finally:
        conn.close()
        os.unlink(db_path)

# T137: Test list all devices with names
def test_list_all_devices_with_names():
    conn, db_path = create_test_db_file()
    try:
        # Add multiple devices
        set_device_name(conn, "hue-001", "Sensor 1", "hue", "Kitchen")
        set_device_name(conn, "hue-002", "Sensor 2", "hue", "Bedroom")
        set_device_name(conn, "amazon-001", "AQM Device", "amazon", "Living Room")
        
        devices = list_devices(conn)
        
        assert len(devices) == 3
        # Check structure (unique_id, device_name, device_type, location)
        device_dict = {d[0]: (d[1], d[2], d[3]) for d in devices}
        assert device_dict["hue-001"] == ("Sensor 1", "hue", "Kitchen")
        assert device_dict["hue-002"] == ("Sensor 2", "hue", "Bedroom")
        assert device_dict["amazon-001"] == ("AQM Device", "amazon", "Living Room")
    finally:
        conn.close()
        os.unlink(db_path)
