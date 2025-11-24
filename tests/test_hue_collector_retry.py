"""
Tests for Hue collector retry logic integration.

Sprint: 005-system-reliability
Phase: 4 - User Story 2 (Universal Retry Logic)
Tasks: T045-T049
"""

import pytest
from unittest import mock
import sys
import requests

# Mock phue before importing hue_collector to avoid import errors
sys.modules['phue'] = mock.MagicMock()

from source.collectors import hue_collector


# T045: test_hue_network_timeout_retry
def test_hue_network_timeout_retry():
    """Verify Hue collector retries on network timeout errors."""
    config = {
        'collectors': {
            'hue': {
                'retry_attempts': 3,
                'retry_backoff_base': 1,
            }
        }
    }
    
    sensor_info = {
        'sensor_id': 'test_sensor_1',
        'unique_id': 'abc123',
        'location': 'Living Room',
    }
    
    # Mock bridge object
    mock_bridge = mock.MagicMock()
    mock_bridge.username = 'test_api_key'
    mock_bridge.ip = '192.168.1.100'
    
    # Simulate timeout on first 2 attempts, then success
    with mock.patch('requests.get') as mock_get:
        mock_get.side_effect = [
            requests.Timeout("Connection timeout"),
            requests.Timeout("Connection timeout"),
            mock.MagicMock(
                status_code=200,
                json=lambda: {
                    'config': {'reachable': True},
                    'state': {'temperature': 2134},
                }
            )
        ]
        
        # Should succeed after retries
        reading = hue_collector.collect_reading_from_sensor(
            mock_bridge, 'test_sensor_1', sensor_info, config
        )
        
        assert reading is not None
        assert reading['temperature_celsius'] == 21.34
        assert mock_get.call_count == 3  # 2 failures + 1 success


# T046: test_hue_bridge_unreachable_retry
def test_hue_bridge_unreachable_retry():
    """Verify Hue collector retries when bridge is unreachable."""
    config = {
        'collectors': {
            'hue': {
                'retry_attempts': 3,
                'retry_backoff_base': 1,
            }
        }
    }
    
    sensor_info = {
        'sensor_id': 'test_sensor_1',
        'unique_id': 'abc123',
        'location': 'Kitchen',
    }
    
    mock_bridge = mock.MagicMock()
    mock_bridge.username = 'test_api_key'
    mock_bridge.ip = '192.168.1.100'
    
    # Simulate connection error, then success
    with mock.patch('requests.get') as mock_get:
        mock_get.side_effect = [
            requests.ConnectionError("Bridge unreachable"),
            mock.MagicMock(
                status_code=200,
                json=lambda: {
                    'config': {'reachable': True},
                    'state': {'temperature': 1980},
                }
            )
        ]
        
        reading = hue_collector.collect_reading_from_sensor(
            mock_bridge, 'test_sensor_1', sensor_info, config
        )
        
        assert reading is not None
        assert reading['temperature_celsius'] == 19.80
        assert mock_get.call_count == 2


# T047: test_hue_rate_limit_backoff
def test_hue_rate_limit_backoff():
    """Verify Hue collector handles rate limiting with exponential backoff."""
    config = {
        'collectors': {
            'hue': {
                'retry_attempts': 3,
                'retry_backoff_base': 2,
            }
        }
    }
    
    sensor_info = {
        'sensor_id': 'test_sensor_1',
        'unique_id': 'abc123',
        'location': 'Bedroom',
    }
    
    mock_bridge = mock.MagicMock()
    mock_bridge.username = 'test_api_key'
    mock_bridge.ip = '192.168.1.100'
    
    # Simulate HTTP 429 (rate limit) error
    with mock.patch('requests.get') as mock_get:
        rate_limit_response = mock.MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.raise_for_status.side_effect = requests.HTTPError("429 Too Many Requests")
        
        success_response = mock.MagicMock(
            status_code=200,
            json=lambda: {
                'config': {'reachable': True},
                'state': {'temperature': 2250},
            }
        )
        
        mock_get.side_effect = [
            rate_limit_response,
            success_response
        ]
        
        # Should retry with backoff and succeed
        with mock.patch('time.sleep') as mock_sleep:
            reading = hue_collector.collect_reading_from_sensor(
                mock_bridge, 'test_sensor_1', sensor_info, config
            )
            
            assert reading is not None
            assert reading['temperature_celsius'] == 22.50
            # Verify backoff was applied (base_delay * backoff^0 = 2 * 1 = 2s)
            assert mock_sleep.call_count >= 1


# T048: test_hue_permanent_error_no_retry
def test_hue_permanent_error_no_retry():
    """Verify Hue collector does not retry on permanent errors (sensor offline)."""
    config = {
        'collectors': {
            'hue': {
                'retry_attempts': 3,
                'retry_backoff_base': 1,
            }
        }
    }
    
    sensor_info = {
        'sensor_id': 'test_sensor_1',
        'unique_id': 'abc123',
        'location': 'Garage',
    }
    
    mock_bridge = mock.MagicMock()
    mock_bridge.username = 'test_api_key'
    mock_bridge.ip = '192.168.1.100'
    
    # Sensor is unreachable (permanent condition)
    with mock.patch('requests.get') as mock_get:
        mock_get.return_value = mock.MagicMock(
            status_code=200,
            json=lambda: {
                'config': {'reachable': False},  # Sensor offline
                'state': {'temperature': 2000},
            }
        )
        
        # Should not retry, just return None
        reading = hue_collector.collect_reading_from_sensor(
            mock_bridge, 'test_sensor_1', sensor_info, config
        )
        
        assert reading is None
        assert mock_get.call_count == 1  # No retries


# T049: test_hue_retry_exhaustion_continues
def test_hue_retry_exhaustion_continues():
    """Verify collector continues to next sensor after retry exhaustion."""
    config = {
        'collectors': {
            'hue': {
                'retry_attempts': 3,  # Matches decorator default
                'retry_backoff_base': 1,
                'collection_interval': 300,
            }
        }
    }
    
    sensor_info = {
        'sensor_id': 'test_sensor_1',
        'unique_id': 'abc123',
        'location': 'Office',
    }
    
    mock_bridge = mock.MagicMock()
    mock_bridge.username = 'test_api_key'
    mock_bridge.ip = '192.168.1.100'
    
    # All attempts fail
    with mock.patch('requests.get') as mock_get:
        mock_get.side_effect = requests.Timeout("Connection timeout")
        
        # Should exhaust retries and return None (not crash)
        reading = hue_collector.collect_reading_from_sensor(
            mock_bridge, 'test_sensor_1', sensor_info, config
        )
        
        assert reading is None
        assert mock_get.call_count == 3  # max_attempts = 3
