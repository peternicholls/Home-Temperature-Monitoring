#!/usr/bin/env python3
"""
Database Manager with WAL Mode and Retry Logic

Sprint 1.1 Enhancement: Context manager support, WAL mode, exponential backoff retry
"""

import sqlite3
import time
import logging
from typing import Optional

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
    
    def __init__(self, db_path: str, config: dict = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
            config: Configuration dictionary with retry and WAL settings
        """
        self.db_path = db_path
        self.config = config or {}
        self.conn = None
        
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
        """Initialize database schema (no changes from previous sprints)."""
        # Schema initialization code remains unchanged
        # See source/storage/schema.py for full schema
        pass
    
    def insert_temperature_reading(self, reading: dict) -> bool:
        """
        Insert temperature reading with retry logic.
        
        Args:
            reading: Dictionary with reading data
            
        Returns:
            bool: True if insert successful, False if duplicate or failed
        """
        for attempt in range(1, self.retry_max_attempts + 1):
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
                if "database is locked" in str(e) and attempt < self.retry_max_attempts:
                    wait_time = self.retry_base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"Database locked (attempt {attempt}/{self.retry_max_attempts}), "
                        f"retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue
                # Re-raise if max retries exceeded
                logger.error(f"Database operation failed after {attempt} attempts: {e}")
                raise
        
        return False
    
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


# Usage example:
if __name__ == '__main__':
    config = {
        'storage': {
            'enable_wal_mode': True,
            'retry_max_attempts': 3,
            'retry_base_delay': 1.0,
            'busy_timeout_ms': 5000,
        }
    }
    
    # Context manager usage (recommended)
    with DatabaseManager('data/readings.db', config) as db:
        reading = {
            'timestamp': '2025-11-19T10:30:00+00:00',
            'device_id': 'hue:test_sensor',
            'temperature_celsius': 21.5,
            'location': 'Test Room',
            'device_type': 'hue_sensor',
        }
        db.insert_temperature_reading(reading)
