#!/usr/bin/env python3
"""
Database Manager with WAL Mode and Retry Logic

Sprint: 005-system-reliability (enhanced)
Enhancements: Enhanced WAL mode verification, checkpoint configuration, comprehensive logging,
              @retry_with_backoff integration for resilient database operations
"""

import sqlite3
import time
import logging
from .schema import SCHEMA_SQL
from source.utils.retry import retry_with_backoff

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
            try:
                cursor = self.conn.execute("PRAGMA journal_mode=WAL")
                actual_mode = cursor.fetchone()[0]
                
                if actual_mode.lower() == 'wal':
                    logger.info(f"✓ WAL mode enabled successfully for database: {self.db_path}")
                else:
                    logger.warning(
                        f"WAL mode requested but database is in {actual_mode} mode. "
                        f"Continuing with {actual_mode} mode."
                    )
            except Exception as e:
                logger.error(
                    f"Failed to enable WAL mode: {e}. "
                    f"Falling back to default journal mode. "
                    f"This may impact concurrent access performance."
                )
        
        # Configure WAL checkpoint interval
        if self.enable_wal and self.wal_checkpoint_interval > 0:
            try:
                self.conn.execute(f"PRAGMA wal_autocheckpoint={self.wal_checkpoint_interval}")
                logger.debug(f"WAL checkpoint interval set to {self.wal_checkpoint_interval} pages")
            except Exception as e:
                logger.warning(f"Failed to configure WAL checkpoint interval: {e}")
        
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
        
        # Check if device_registry table exists
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='device_registry'"
        )
        device_registry_exists = cursor.fetchone() is not None
        
        if not device_registry_exists:
            # Create device_registry table (new in Sprint 005)
            logger.info("Creating device_registry table for device naming feature...")
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS device_registry (
                    device_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_type TEXT NOT NULL,
                    device_name TEXT,
                    location TEXT,
                    unique_id TEXT NOT NULL UNIQUE,
                    model_info TEXT,
                    first_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                );
                CREATE INDEX IF NOT EXISTS idx_device_unique_id ON device_registry(unique_id);
                CREATE INDEX IF NOT EXISTS idx_device_type ON device_registry(device_type);
                CREATE INDEX IF NOT EXISTS idx_device_active ON device_registry(is_active) WHERE is_active = 1;
            """)
            self.conn.commit()
            logger.info("✓ Device registry table created successfully")

    def insert_reading(self, reading: dict):
        """
        Insert a reading into the database.
        
        Args:
            reading: Dictionary with reading data
        
        Note: For production use, prefer insert_temperature_reading() which has retry logic.
        """
        keys = ', '.join(reading.keys())
        placeholders = ', '.join(['?' for _ in reading])
        sql = f"INSERT INTO readings ({keys}) VALUES ({placeholders})"
        self.conn.execute(sql, tuple(reading.values()))
        self.conn.commit()

    def _perform_insert(self, reading: dict) -> bool:
        """
        Internal method to perform database insert.
        Wrapped by retry decorator in insert_temperature_reading().
        
        Returns:
            bool: True if insert successful
            
        Raises:
            sqlite3.IntegrityError: For duplicate readings (UNIQUE constraint)
            sqlite3.OperationalError: For database locked errors (will be retried)
        """
        keys = ', '.join(reading.keys())
        placeholders = ', '.join(['?' for _ in reading])
        sql = f"INSERT INTO readings ({keys}) VALUES ({placeholders})"
        self.conn.execute(sql, tuple(reading.values()))
        self.conn.commit()
        return True

    def insert_temperature_reading(self, reading: dict, max_retries: int = None) -> bool:
        """
        Insert a temperature reading with UNIQUE constraint handling and retry logic.
        
        This method uses @retry_with_backoff for transient database lock errors.
        
        Args:
            reading: Dictionary with reading data
            max_retries: Number of retry attempts for database locked errors (uses config if None)
            
        Returns:
            bool: True if insert successful, False if duplicate reading
            
        Raises:
            sqlite3.OperationalError: If database remains locked after all retries
        """
        if max_retries is None:
            max_retries = self.retry_max_attempts
        
        # Create a retry-wrapped version of _perform_insert
        @retry_with_backoff(
            max_attempts=max_retries,
            base_delay=self.retry_base_delay,
            backoff_multiplier=2.0,
            transient_exceptions=(sqlite3.OperationalError,),
            permanent_exceptions=(sqlite3.IntegrityError,)
        )
        def insert_with_retry():
            return self._perform_insert(reading)
        
        try:
            return insert_with_retry()
            
        except sqlite3.IntegrityError as e:
            # Handle UNIQUE constraint violation (duplicate reading)
            if "UNIQUE constraint failed" in str(e):
                logger.debug("Duplicate reading detected, skipping")
                return False
            # Re-raise other integrity errors
            raise

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
    def verify_wal_mode(self) -> bool:
        """
        Verify WAL mode is currently enabled.
        
        Returns:
            bool: True if WAL mode is enabled
        """
        try:
            cursor = self.conn.execute("PRAGMA journal_mode")
            mode = cursor.fetchone()[0]
            return mode.lower() == 'wal'
        except Exception as e:
            logger.error(f"Failed to verify WAL mode: {e}")
            return False
    
    def get_wal_checkpoint_interval(self) -> int:
        """
        Get current WAL checkpoint interval.
        
        Returns:
            int: Checkpoint interval in pages, or 0 if not set
        """
        try:
            cursor = self.conn.execute("PRAGMA wal_autocheckpoint")
            interval = cursor.fetchone()[0]
            return int(interval) if interval else 0
        except Exception as e:
            logger.error(f"Failed to get WAL checkpoint interval: {e}")
            return 0
    
    def test_write_with_rollback(self) -> bool:
        """
        Test database write capability with rollback.
        
        Returns:
            bool: True if write successful
            
        Raises:
            PermissionError: If database is not writable
            Exception: For other database errors
        """
        try:
            # Use a transaction to test write and rollback
            self.conn.execute("BEGIN TRANSACTION")
            
            # Attempt test insert
            test_data = {
                "timestamp": "1970-01-01T00:00:00+00:00",
                "device_id": "health_check:test",
                "temperature_celsius": 20.0,
                "location": "test",
                "device_type": "health_check"
            }
            
            keys = ', '.join(test_data.keys())
            placeholders = ', '.join(['?' for _ in test_data])
            sql = f"INSERT INTO readings ({keys}) VALUES ({placeholders})"
            self.conn.execute(sql, tuple(test_data.values()))
            
            # Rollback to avoid polluting data
            self.conn.execute("ROLLBACK")
            
            return True
            
        except sqlite3.OperationalError as e:
            self.conn.execute("ROLLBACK")
            if "readonly" in str(e).lower() or "permission" in str(e).lower():
                raise PermissionError(f"Database is not writable: {e}")
            raise
        except Exception as e:
            try:
                self.conn.execute("ROLLBACK")
            except:
                pass
            raise


# Legacy alias for backward compatibility
StorageManager = DatabaseManager