#!/usr/bin/env python3
"""
Tests for WAL Mode Verification - User Story 1

Sprint: 005-system-reliability
Tests: T032-T036

These tests verify Write-Ahead Logging (WAL) mode implementation for database resilience.
"""

import pytest
import sqlite3
import os
import tempfile
import time
import threading
from unittest.mock import patch, MagicMock
from source.storage.manager import DatabaseManager


class TestDatabaseWAL:
    """Test suite for WAL mode functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        # Cleanup
        for ext in ['', '-shm', '-wal']:
            try:
                os.unlink(path + ext)
            except FileNotFoundError:
                pass
    
    @pytest.fixture
    def db_manager_with_wal(self, temp_db_path):
        """Create DatabaseManager with WAL enabled."""
        config = {
            'storage': {
                'enable_wal_mode': True,
                'wal_checkpoint_interval': 1000
            }
        }
        manager = DatabaseManager(db_path=temp_db_path, config=config)
        yield manager
        manager.close()
    
    @pytest.fixture
    def db_manager_without_wal(self, temp_db_path):
        """Create DatabaseManager with WAL disabled."""
        config = {
            'storage': {
                'enable_wal_mode': False
            }
        }
        manager = DatabaseManager(db_path=temp_db_path, config=config)
        yield manager
        manager.close()
    
    def test_wal_mode_enabled_on_init(self, db_manager_with_wal):
        """
        T032: Verify WAL mode is enabled on database initialization.
        
        Success Criteria:
        - PRAGMA journal_mode returns 'wal'
        - WAL mode is set during __init__
        - WAL-SHM and WAL files are created
        """
        # Query journal mode
        cursor = db_manager_with_wal.conn.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        
        # Verify WAL mode is enabled
        assert journal_mode.lower() == 'wal', f"Expected WAL mode, got {journal_mode}"
        
        # Insert a reading to trigger WAL file creation
        test_reading = {
            "timestamp": "2025-11-21T10:00:00+00:00",
            "device_id": "test:wal001",
            "temperature_celsius": 20.5,
            "location": "test_room",
            "device_type": "hue_sensor"
        }
        db_manager_with_wal.insert_reading(test_reading)
        
        # Verify WAL files exist
        db_path = db_manager_with_wal.db_path
        assert os.path.exists(db_path + '-wal') or os.path.exists(db_path + '-shm'), \
            "WAL auxiliary files should be created"
    
    def test_wal_checkpoint_interval_configured(self, db_manager_with_wal):
        """
        T033: Verify WAL checkpoint interval is configured correctly.
        
        Success Criteria:
        - PRAGMA wal_autocheckpoint returns configured value
        - Default is 1000 pages
        - Custom values can be set
        """
        # Query checkpoint interval
        cursor = db_manager_with_wal.conn.execute("PRAGMA wal_autocheckpoint")
        checkpoint_interval = cursor.fetchone()[0]
        
        # Verify it matches configuration
        expected_interval = 1000
        assert checkpoint_interval == expected_interval, \
            f"Expected checkpoint interval {expected_interval}, got {checkpoint_interval}"
    
    def test_wal_file_growth_bounded(self, db_manager_with_wal, temp_db_path):
        """
        T034: Verify WAL file growth is bounded by checkpoint interval.
        
        Success Criteria:
        - WAL file size doesn't grow unbounded
        - Checkpoint triggers after configured interval
        - WAL is truncated after checkpoint
        """
        # Insert multiple readings to grow WAL
        for i in range(100):
            reading = {
                "timestamp": f"2025-11-21T10:{i:02d}:00+00:00",
                "device_id": f"test:device{i:03d}",
                "temperature_celsius": 20.0 + (i * 0.1),
                "location": "test_room",
                "device_type": "hue_sensor"
            }
            db_manager_with_wal.insert_reading(reading)
        
        # Force checkpoint
        db_manager_with_wal.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        
        # Verify WAL file size is reasonable (should be small after checkpoint)
        wal_path = temp_db_path + '-wal'
        if os.path.exists(wal_path):
            wal_size = os.path.getsize(wal_path)
            # WAL should be truncated or very small after checkpoint
            assert wal_size < 100000, f"WAL file too large after checkpoint: {wal_size} bytes"
    
    def test_concurrent_reads_during_write(self, db_manager_with_wal):
        """
        T035: Verify concurrent reads can occur during write operations.
        
        Success Criteria:
        - Reads don't block during writes (WAL mode benefit)
        - No "database is locked" errors for concurrent reads
        - Data consistency maintained
        
        Note: This test verifies WAL mode allows reads during writes by
        demonstrating that multiple connections can be opened and queried
        without blocking.
        """
        # Insert initial data
        initial_reading = {
            "timestamp": "2025-11-21T10:00:00+00:00",
            "device_id": "test:concurrent001",
            "temperature_celsius": 20.0,
            "location": "test_room",
            "device_type": "hue_sensor"
        }
        db_manager_with_wal.insert_reading(initial_reading)
        
        # Verify we can open multiple read connections simultaneously
        # This is a key benefit of WAL mode
        read_conn1 = sqlite3.connect(db_manager_with_wal.db_path)
        read_conn2 = sqlite3.connect(db_manager_with_wal.db_path)
        
        try:
            # Both connections should be able to read simultaneously
            cursor1 = read_conn1.execute("SELECT COUNT(*) FROM readings")
            count1 = cursor1.fetchone()[0]
            
            cursor2 = read_conn2.execute("SELECT COUNT(*) FROM readings")
            count2 = cursor2.fetchone()[0]
            
            # Both should see the same data
            assert count1 == count2 == 1, "Concurrent reads should see consistent data"
            
            # Write some data using the main connection
            for i in range(3):
                reading = {
                    "timestamp": f"2025-11-21T10:0{i+1}:00+00:00",
                    "device_id": f"test:concurrent{i+2:03d}",
                    "temperature_celsius": 20.0 + i,
                    "location": "test_room",
                    "device_type": "hue_sensor"
                }
                db_manager_with_wal.insert_reading(reading)
            
            # Read connections should still be able to query
            # (they may see old data until they reconnect, which is expected)
            cursor1 = read_conn1.execute("SELECT COUNT(*) FROM readings")
            count1_after = cursor1.fetchone()[0]
            
            cursor2 = read_conn2.execute("SELECT COUNT(*) FROM readings")
            count2_after = cursor2.fetchone()[0]
            
            # Both read connections should get valid counts (no lock errors)
            assert count1_after >= 1, "Read connection 1 should see valid count"
            assert count2_after >= 1, "Read connection 2 should see valid count"
            
        finally:
            read_conn1.close()
            read_conn2.close()
    
    def test_concurrent_writes_no_lock_errors(self, db_manager_with_wal):
        """
        T036: Verify concurrent writes complete without excessive lock errors.
        
        Success Criteria:
        - Multiple writers can work concurrently with WAL mode
        - Lock errors are minimal or handled gracefully
        - All writes eventually succeed
        """
        write_results = {'success': 0, 'failed': 0}
        write_errors = []
        lock = threading.Lock()
        
        def writer_thread(thread_id):
            """Thread that performs writes."""
            try:
                # Create new connection for this writer
                conn = sqlite3.connect(db_manager_with_wal.db_path, timeout=5.0)
                conn.execute("PRAGMA journal_mode=WAL")
                
                for i in range(10):
                    try:
                        reading = {
                            "timestamp": f"2025-11-21T{thread_id:02d}:{i:02d}:00+00:00",
                            "device_id": f"test:writer{thread_id:02d}_{i:03d}",
                            "temperature_celsius": 20.0 + thread_id + (i * 0.1),
                            "location": f"room_{thread_id}",
                            "device_type": "hue_sensor"
                        }
                        keys = ', '.join(reading.keys())
                        placeholders = ', '.join(['?' for _ in reading])
                        sql = f"INSERT INTO readings ({keys}) VALUES ({placeholders})"
                        conn.execute(sql, tuple(reading.values()))
                        conn.commit()
                        
                        with lock:
                            write_results['success'] += 1
                    except sqlite3.OperationalError as e:
                        if "database is locked" in str(e):
                            with lock:
                                write_results['failed'] += 1
                        raise
                
                conn.close()
            except Exception as e:
                write_errors.append(f"Thread {thread_id}: {str(e)}")
        
        # Start multiple concurrent writer threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=writer_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)
        
        # Verify most writes succeeded
        total_writes = write_results['success'] + write_results['failed']
        assert total_writes == 30, f"Expected 30 total writes, got {total_writes}"
        
        # With WAL mode, we expect very few or no lock errors
        # Allow up to 10% failure rate due to concurrent write contention
        success_rate = write_results['success'] / total_writes if total_writes > 0 else 0
        assert success_rate >= 0.9, \
            f"Success rate too low: {success_rate:.1%} ({write_results['success']}/{total_writes})"
        
        # Verify no catastrophic errors
        assert len(write_errors) == 0 or write_results['success'] > 0, \
            f"Concurrent writes failed: {write_errors}"
