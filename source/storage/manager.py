import sqlite3
from .schema import SCHEMA_SQL

DB_PATH = "data/readings.db"

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.init_schema()

    def init_schema(self):
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def insert_reading(self, reading: dict):
        keys = ', '.join(reading.keys())
        placeholders = ', '.join(['?' for _ in reading])
        sql = f"INSERT INTO readings ({keys}) VALUES ({placeholders})"
        self.conn.execute(sql, tuple(reading.values()))
        self.conn.commit()

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
