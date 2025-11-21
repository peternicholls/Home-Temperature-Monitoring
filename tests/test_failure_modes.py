"""
Integration tests for failure mode simulation.
Sprint: 005-system-reliability
Phase: 8
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from source.collectors.hue_collector import collect_reading_from_sensor
from source.collectors.amazon_collector import AmazonAQMCollector
from source.utils.retry import TransientError, PermanentError
from source.storage.manager import StorageManager
from source.utils.logging import setup_logging
import sqlite3
import os
import shutil

class TestFailureModes:
    """Test system behavior under various failure scenarios."""

    @pytest.mark.asyncio
    async def test_network_disconnection_retry(self):
        """T105: Test network disconnection for both collectors and verify retry logic."""
        # Hue Collector Network Failure
        # We mock requests.get to fail twice then succeed
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [
                Exception("Connection refused"),
                Exception("Connection refused"),
                Mock(status_code=200, json=lambda: {"state": {"temperature": 2000}, "config": {"reachable": True}})
            ]
            
            # Mock bridge and config
            mock_bridge = Mock()
            mock_bridge.ip = "192.168.1.100"
            mock_bridge.username = "test-user"
            
            config = {"collectors": {"hue": {"retry_attempts": 3, "retry_backoff_base": 0.01}}}
            sensor_info = {"sensor_id": "1", "unique_id": "123", "location": "Test"}
            
            # Call the function
            result = collect_reading_from_sensor(mock_bridge, "1", sensor_info, config)
            
            # Verify it retried and eventually succeeded
            assert result is not None
            assert result['temperature_celsius'] == 20.0
            assert mock_get.call_count == 3

    def test_database_lock_contention(self):
        """T107: Test database lock contention under concurrent writes."""
        # Simulate database locked error
        # We need to mock the connection and cursor used by StorageManager
        
        # Since StorageManager creates a new connection in __enter__, we mock sqlite3.connect
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Mock fetchall for init_schema
            mock_cursor.fetchall.return_value = []
            # Mock fetchone for verify_wal_mode
            mock_cursor.fetchone.return_value = ('wal',)
            
            # We need to mock conn.execute since _perform_insert calls self.conn.execute
            mock_conn.execute.side_effect = [
                sqlite3.OperationalError("database is locked"),
                sqlite3.OperationalError("database is locked"),
                None
            ]
            
            with patch.object(StorageManager, '_connect'):
                manager = StorageManager("test.db")
                # Manually set connection since we mocked _connect
                manager.conn = mock_conn
                
                reading = {
                    'timestamp': '2023-01-01T00:00:00',
                    'device_id': 'test',
                    'temperature_celsius': 20.0,
                    'location': 'test',
                    'device_type': 'test'
                }
                
                manager.insert_temperature_reading(reading)
                
                # Verify retries
                assert mock_conn.execute.call_count == 3

    def test_log_rotation_low_disk_space(self):
        """T108: Test low disk space handling for log rotation."""
        # Mock shutil.disk_usage to return low space
        with patch('shutil.disk_usage') as mock_usage:
            # Total, Used, Free
            mock_usage.return_value = (100, 95, 5) # 5 bytes free
            
            # Setup logging should handle this gracefully
            # We need to verify it doesn't crash
            try:
                config = {
                    "logging": {
                        "log_file_path": "logs/test.log",
                        "enable_file_logging": True
                    }
                }
                setup_logging(config=config)
            except Exception as e:
                pytest.fail(f"setup_logging crashed on low disk space: {e}")

    @pytest.mark.asyncio
    async def test_amazon_rate_limiting(self):
        """T106: Test API rate limiting and verify backoff behavior."""
        # Mock httpx.AsyncClient.post to return 429 then 200
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response_429 = Mock()
            mock_response_429.status_code = 429
            mock_response_429.text = "Rate Limit Exceeded"
            
            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"data": {"endpoints": {"items": []}}}
            
            mock_post.side_effect = [mock_response_429, mock_response_429, mock_response_200]
            
            collector = AmazonAQMCollector({"csrf": "test"}, config={"collection": {"retry_attempts": 3, "retry_backoff_base": 0.01}})
            
            # Call list_devices which uses retry
            await collector.list_devices()
            
            # Verify retries
            assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_amazon_token_expiration(self):
        """T110: Test OAuth token expiration and alert file creation."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response_401 = Mock()
            mock_response_401.status_code = 401
            
            mock_post.return_value = mock_response_401
            
            collector = AmazonAQMCollector({"csrf": "test"}, config={"collection": {"retry_attempts": 1, "retry_backoff_base": 0.01}})
            
            # Mock alert file path
            with patch('pathlib.Path.write_text') as mock_write:
                await collector.get_air_quality_readings("entity_id")
                
                # Verify alert file created
                mock_write.assert_called_once()
                assert "token refresh required" in mock_write.call_args[0][0]


