import sqlite3
import time
from .schema import SCHEMA_SQL

DB_PATH = "data/readings.db"

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.init_schema()

    def init_schema(self):
        """Initialize schema with migration support for existing databases."""
        # Check if table exists and what columns it has
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='readings'"
        )
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Get existing columns
            cursor = self.conn.execute("PRAGMA table_info(readings)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            
            # Add missing columns if needed
            required_cols = {
                'is_anomalous', 'humidity_percent', 'battery_level', 'signal_strength',
                'thermostat_mode', 'thermostat_state', 'day_night', 'weather_conditions',
                'raw_response', 'created_at'
            }
            
            for col in required_cols - existing_cols:
                if col == 'is_anomalous':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN is_anomalous BOOLEAN DEFAULT 0")
                elif col == 'humidity_percent':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN humidity_percent REAL")
                elif col == 'battery_level':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN battery_level INTEGER")
                elif col == 'signal_strength':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN signal_strength INTEGER")
                elif col == 'thermostat_mode':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN thermostat_mode TEXT")
                elif col == 'thermostat_state':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN thermostat_state TEXT")
                elif col == 'day_night':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN day_night TEXT")
                elif col == 'weather_conditions':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN weather_conditions TEXT")
                elif col == 'raw_response':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN raw_response TEXT")
                elif col == 'created_at':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            
            self.conn.commit()
        else:
            # Table doesn't exist, create from schema
            self.conn.executescript(SCHEMA_SQL)
            self.conn.commit()

    def insert_reading(self, reading: dict):
        keys = ', '.join(reading.keys())
        placeholders = ', '.join(['?' for _ in reading])
        sql = f"INSERT INTO readings ({keys}) VALUES ({placeholders})"
        self.conn.execute(sql, tuple(reading.values()))
        self.conn.commit()

    def insert_temperature_reading(self, reading: dict, max_retries: int = 3):
        """
        Insert a temperature reading with UNIQUE constraint handling and retry logic.
        
        Args:
            reading: Dictionary with reading data
            max_retries: Number of retry attempts for database locked errors
            
        Returns:
            bool: True if insert successful, False if duplicate or failed
        """
        for attempt in range(max_retries):
            try:
                keys = ', '.join(reading.keys())
                placeholders = ', '.join(['?' for _ in reading])
                sql = f"INSERT INTO readings ({keys}) VALUES ({placeholders})"
                self.conn.execute(sql, tuple(reading.values()))
                self.conn.commit()
                return True
            except sqlite3.IntegrityError as e:
                # Handle UNIQUE constraint violation (duplicate reading)
                if "UNIQUE constraint failed" in str(e):
                    return False  # Duplicate, skip silently
                raise  # Re-raise other integrity errors
            except sqlite3.OperationalError as e:
                # Handle database locked errors with exponential backoff
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    time.sleep(wait_time)
                    continue
                raise  # Re-raise if max retries exceeded
        return False

    def insert_sample_reading(self):
        sample = {
            "timestamp": "2025-11-18T14:30:00+00:00",
            "device_id": "test:device001",
            "temperature_celsius": 21.5,
            "location": "test_location",
            "device_type": "hue_sensor"
        }
        self.insert_reading(sample)

    def query_readings(self, where: str = None, params: tuple = ()): 
        sql = "SELECT * FROM readings"
        if where:
            sql += f" WHERE {where}"
        return self.conn.execute(sql, params).fetchall()

    def close(self):
        self.conn.close()
