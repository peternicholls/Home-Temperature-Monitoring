#!/usr/bin/env python3
"""
Database Manager with WAL Mode and Retry Logic

Sprint 1.1 Enhancement: Context manager support, WAL mode, exponential backoff retry
"""

import sqlite3
import time
import logging
from .schema import SCHEMA_SQL

DB_PATH = "data/readings.db"
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database connections with WAL mode and retry logic.
    
    Features:
    - Write-Ahead Logging (WAL) mode for concurrent reads during writes
    - Exponential backoff retry for transient lock errors
    - Context manager protocol for automatic resource cleanup
    - Thread-safe connection handling
    """
    
    def __init__(self, db_path: str = DB_PATH, config: dict = {}):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
            config: Configuration dictionary with retry and WAL settings
        """
        self.db_path = db_path
        self.config = config or {}
        
        # Extract configuration
        storage_config = self.config.get('storage', {})
        self.enable_wal = storage_config.get('enable_wal_mode', True)
        self.wal_checkpoint_interval = storage_config.get('wal_checkpoint_interval', 1000)
        self.retry_max_attempts = storage_config.get('retry_max_attempts', 3)
        self.retry_base_delay = storage_config.get('retry_base_delay', 1.0)
        self.busy_timeout_ms = storage_config.get('busy_timeout_ms', 5000)
        
        # Initialize connection
        self._connect()

    def _connect(self):
        """Establish database connection with WAL mode and timeout settings."""
        self.conn = sqlite3.connect(self.db_path, timeout=self.busy_timeout_ms / 1000.0)
        
        # Enable WAL mode for concurrent read/write
        if self.enable_wal:
            self.conn.execute("PRAGMA journal_mode=WAL")
            logger.info("WAL mode enabled for database")
        
        # Configure WAL checkpoint interval
        if self.wal_checkpoint_interval > 0:
            self.conn.execute(f"PRAGMA wal_autocheckpoint={self.wal_checkpoint_interval}")
        
        # Initialize schema
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
                'raw_response', 'created_at', 'pm25_ugm3', 'voc_ppb', 'co_ppm', 'co2_ppm', 'iaq_score'
            }
            
            for col in required_cols - existing_cols:
                if col == 'is_anomalous':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN is_anomalous BOOLEAN DEFAULT 0")
                elif col == 'humidity_percent':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN humidity_percent REAL CHECK(humidity_percent IS NULL OR (humidity_percent >= 0 AND humidity_percent <= 100))")
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
                elif col == 'pm25_ugm3':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN pm25_ugm3 REAL CHECK(pm25_ugm3 IS NULL OR pm25_ugm3 >= 0)")
                elif col == 'voc_ppb':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN voc_ppb REAL CHECK(voc_ppb IS NULL OR voc_ppb >= 0)")
                elif col == 'co_ppm':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN co_ppm REAL CHECK(co_ppm IS NULL OR co_ppm >= 0)")
                elif col == 'co2_ppm':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN co2_ppm REAL CHECK(co2_ppm IS NULL OR co2_ppm >= 0)")
                elif col == 'iaq_score':
                    self.conn.execute("ALTER TABLE readings ADD COLUMN iaq_score REAL CHECK(iaq_score IS NULL OR (iaq_score >= 0 AND iaq_score <= 100))")
            
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

    def insert_temperature_reading(self, reading: dict, max_retries: int = None) -> bool:
        """
        Insert a temperature reading with UNIQUE constraint handling and retry logic.
        
        Args:
            reading: Dictionary with reading data
            max_retries: Number of retry attempts for database locked errors (uses config if None)
            
        Returns:
            bool: True if insert successful, False if duplicate or failed
        """
        if max_retries is None:
            max_retries = self.retry_max_attempts
        
        for attempt in range(1, max_retries + 1):
            try:
                keys = ', '.join(reading.keys())
                placeholders = ', '.join(['?' for _ in reading])
                sql = f"INSERT INTO readings ({keys}) VALUES ({placeholders})"
                self.conn.execute(sql, tuple(reading.values()))
                self.conn.commit()
                
                if attempt > 1:
                    logger.info(f"Insert succeeded on retry attempt {attempt}")
                
                return True
                
            except sqlite3.IntegrityError as e:
                # Handle UNIQUE constraint violation (duplicate reading)
                if "UNIQUE constraint failed" in str(e):
                    logger.debug("Duplicate reading detected, skipping")
                    return False
                # Re-raise other integrity errors
                raise
                
            except sqlite3.OperationalError as e:
                # Handle database locked errors with exponential backoff
                if "database is locked" in str(e) and attempt < max_retries:
                    wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"Database locked (attempt {attempt}/{max_retries}), "
                        f"retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue
                # Re-raise if max retries exceeded
                logger.error(f"Database operation failed after {attempt} attempts: {e}")
                raise
        
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

    def query_readings(self, where: str = '', params: tuple = ()): 
        sql = "SELECT * FROM readings"
        if where:
            sql += f" WHERE {where}"
        return self.conn.execute(sql, params).fetchall()

    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed."""
        self.close()
        return False  # Don't suppress exceptions

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")
