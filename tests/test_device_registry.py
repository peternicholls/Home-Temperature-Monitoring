
import pytest
import sqlite3
from contextlib import closing
import tempfile
import os

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

def create_test_db_file():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3')
    tmp.close()
    conn = sqlite3.connect(tmp.name)
    with closing(conn.cursor()) as cur:
        cur.executescript(DEVICE_REGISTRY_SCHEMA)
    return conn, tmp.name

# T127: Test device_registry table creation
def test_device_registry_table_creation():
    conn, db_path = create_test_db_file()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("PRAGMA table_info(device_registry);")
            columns = [row[1] for row in cur.fetchall()]
        expected = [
            "device_id", "device_type", "device_name", "location", "unique_id",
            "model_info", "first_seen", "last_seen", "is_active"
        ]
        assert all(col in columns for col in expected)
    finally:
        conn.close()
        os.unlink(db_path)

# T128: Test device insert with name and location
def test_device_insert_with_name_and_location():
    conn, db_path = create_test_db_file()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute(
                """
                INSERT INTO device_registry (device_type, device_name, location, unique_id, model_info, first_seen, last_seen, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("hue", "Living Room Sensor", "Living Room", "hue-123", "HueModelX", "2025-11-21T10:00:00", "2025-11-21T10:00:00", 1)
            )
            conn.commit()
            cur.execute("SELECT device_name, location FROM device_registry WHERE unique_id=?", ("hue-123",))
            row = cur.fetchone()
        assert row == ("Living Room Sensor", "Living Room")
    finally:
        conn.close()
        os.unlink(db_path)

# T129: Test device unique constraint
def test_device_unique_constraint():
    conn, db_path = create_test_db_file()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute(
                """
                INSERT INTO device_registry (device_type, device_name, location, unique_id, model_info, first_seen, last_seen, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("hue", "Sensor1", "Kitchen", "unique-abc", "HueModelY", "2025-11-21T10:00:00", "2025-11-21T10:00:00", 1)
            )
            conn.commit()
            with pytest.raises(sqlite3.IntegrityError):
                cur.execute(
                    """
                    INSERT INTO device_registry (device_type, device_name, location, unique_id, model_info, first_seen, last_seen, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("hue", "Sensor2", "Bedroom", "unique-abc", "HueModelZ", "2025-11-21T10:01:00", "2025-11-21T10:01:00", 1)
                )
    finally:
        conn.close()
        os.unlink(db_path)

# T130: Test device name update
def test_device_name_update():
    conn, db_path = create_test_db_file()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute(
                """
                INSERT INTO device_registry (device_type, device_name, location, unique_id, model_info, first_seen, last_seen, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("hue", "Old Name", "Office", "hue-456", "HueModelA", "2025-11-21T10:00:00", "2025-11-21T10:00:00", 1)
            )
            conn.commit()
            cur.execute("UPDATE device_registry SET device_name=? WHERE unique_id=?", ("New Name", "hue-456"))
            conn.commit()
            cur.execute("SELECT device_name FROM device_registry WHERE unique_id=?", ("hue-456",))
            row = cur.fetchone()
        assert row[0] == "New Name"
    finally:
        conn.close()
        os.unlink(db_path)

# T131: Test device location update
def test_device_location_update():
    conn, db_path = create_test_db_file()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute(
                """
                INSERT INTO device_registry (device_type, device_name, location, unique_id, model_info, first_seen, last_seen, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("hue", "Sensor", "Old Location", "hue-789", "HueModelB", "2025-11-21T10:00:00", "2025-11-21T10:00:00", 1)
            )
            conn.commit()
            cur.execute("UPDATE device_registry SET location=? WHERE unique_id=?", ("New Location", "hue-789"))
            conn.commit()
            cur.execute("SELECT location FROM device_registry WHERE unique_id=?", ("hue-789",))
            row = cur.fetchone()
        assert row[0] == "New Location"
    finally:
        conn.close()
        os.unlink(db_path)
