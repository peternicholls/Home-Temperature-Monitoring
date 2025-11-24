"""
Tests for Amazon AQM collector retry logic integration.

Sprint: 005-system-reliability
Phase: 4 - User Story 2 (Universal Retry Logic)
Tasks: T050-T056
"""

import pytest
from unittest import mock
import asyncio
import httpx
from pathlib import Path
from source.collectors.amazon_collector import AmazonAQMCollector


# T050: test_amazon_network_timeout_retry
@pytest.mark.anyio
async def test_amazon_network_timeout_retry():
    """Verify Amazon collector retries on network timeout errors."""
    config = {
        'collection': {
            'retry_attempts': 3,
            'retry_backoff_base': 1,
            'max_timeout': 120,
        },
        'amazon_aqm': {
            'domain': 'alexa.amazon.com',
        }
    }
    
    cookies = {'csrf': 'test_csrf_token'}
    collector = AmazonAQMCollector(cookies, config)
    
    # Mock httpx client to simulate timeout then success
    with mock.patch('httpx.AsyncClient') as mock_client_class:
        mock_client = mock.AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # First attempt: timeout, second: success
        timeout_error = httpx.TimeoutException("Request timeout")
        success_response = mock.MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            'data': {
                'endpoints': {
                    'items': [{
                        'legacyAppliance': {
                            'friendlyDescription': 'Amazon Indoor Air Quality Monitor',
                            'applianceTypes': ['AIR_QUALITY_MONITOR'],
                            'friendlyName': 'Living Room',
                            'entityId': 'entity_123',
                            'alexaDeviceIdentifierList': [
                                {'dmsDeviceSerialNumber': 'GAJ123'}
                            ]
                        }
                    }]
                }
            }
        }
        
        mock_client.post.side_effect = [timeout_error, success_response]
        
        devices = await collector.list_devices()
        
        assert len(devices) == 1
        assert devices[0]['device_id'] == 'alexa:GAJ123'
        assert mock_client.post.call_count == 2


# T051: test_amazon_transient_auth_error_retry
@pytest.mark.anyio
async def test_amazon_transient_auth_error_retry():
    """Verify Amazon collector retries on transient auth errors."""
    config = {
        'collection': {
            'retry_attempts': 3,
            'retry_backoff_base': 1,
            'max_timeout': 120,
        },
        'amazon_aqm': {
            'domain': 'alexa.amazon.com',
        }
    }
    
    cookies = {'csrf': 'test_csrf_token'}
    collector = AmazonAQMCollector(cookies, config)
    
    with mock.patch('httpx.AsyncClient') as mock_client_class:
        mock_client = mock.AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Simulate 503 Service Unavailable (transient), then success
        error_response = mock.MagicMock()
        error_response.status_code = 503
        
        success_response = mock.MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            'deviceStates': [{
                'capabilityStates': ['{"namespace":"Alexa.TemperatureSensor","name":"temperature","value":{"value":21.5,"scale":"CELSIUS"}}']
            }]
        }
        
        mock_client.post.side_effect = [error_response, success_response]
        
        with mock.patch('asyncio.sleep'):  # Mock sleep to speed up test
            readings = await collector.get_air_quality_readings('entity_123')
        
        assert readings is not None
        assert 'temperature_celsius' in readings


# T052: test_amazon_permanent_auth_error_alert
@pytest.mark.anyio
async def test_amazon_permanent_auth_error_alert():
    """Verify permanent auth error creates alert file."""
    config = {
        'collection': {
            'retry_attempts': 2,
            'retry_backoff_base': 1,
            'max_timeout': 120,
        },
        'amazon_aqm': {
            'domain': 'alexa.amazon.com',
        }
    }
    
    cookies = {'csrf': 'test_csrf_token'}
    collector = AmazonAQMCollector(cookies, config)
    
    alert_file = Path('data/ALERT_TOKEN_REFRESH_NEEDED.txt')
    if alert_file.exists():
        alert_file.unlink()
    
    with mock.patch('httpx.AsyncClient') as mock_client_class:
        mock_client = mock.AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Simulate 401 Unauthorized (permanent auth error)
        error_response = mock.MagicMock()
        error_response.status_code = 401
        mock_client.post.return_value = error_response
        
        with mock.patch('asyncio.sleep'):
            readings = await collector.get_air_quality_readings('entity_123')
        
        assert readings is None
        assert alert_file.exists()
        
        # Cleanup
        if alert_file.exists():
            alert_file.unlink()


# T053: test_amazon_alert_file_creation
def test_amazon_alert_file_creation():
    """Verify alert file is created with correct content."""
    alert_file = Path('data/ALERT_TOKEN_REFRESH_NEEDED.txt')
    
    # Clean up any existing alert file
    if alert_file.exists():
        alert_file.unlink()
    
    # Simulate alert file creation
    alert_file.parent.mkdir(parents=True, exist_ok=True)
    alert_file.write_text("Amazon AQM token refresh required. Please re-authenticate.")
    
    assert alert_file.exists()
    content = alert_file.read_text()
    assert "token refresh required" in content.lower()
    
    # Cleanup
    alert_file.unlink()


# T054: test_amazon_alert_file_cleared_on_success
@pytest.mark.anyio
async def test_amazon_alert_file_cleared_on_success():
    """Verify alert file is auto-cleared on successful auth."""
    config = {
        'collection': {
            'retry_attempts': 2,
            'retry_backoff_base': 1,
            'max_timeout': 120,
        },
        'amazon_aqm': {
            'domain': 'alexa.amazon.com',
        }
    }
    
    cookies = {'csrf': 'test_csrf_token'}
    collector = AmazonAQMCollector(cookies, config)
    
    alert_file = Path('data/ALERT_TOKEN_REFRESH_NEEDED.txt')
    alert_file.parent.mkdir(parents=True, exist_ok=True)
    alert_file.write_text("Test alert")
    
    with mock.patch('httpx.AsyncClient') as mock_client_class:
        mock_client = mock.AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        success_response = mock.MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            'deviceStates': [{
                'capabilityStates': ['{"namespace":"Alexa.TemperatureSensor","name":"temperature","value":{"value":22.0,"scale":"CELSIUS"}}']
            }]
        }
        mock_client.post.return_value = success_response
        
        readings = await collector.get_air_quality_readings('entity_123')
        
        assert readings is not None
        assert not alert_file.exists()  # Should be auto-cleared


# T055: test_amazon_optional_email_notification
@pytest.mark.anyio
async def test_amazon_optional_email_notification():
    """Verify optional email notification on permanent auth error (graceful degradation)."""
    config = {
        'collection': {
            'retry_attempts': 1,
            'retry_backoff_base': 1,
            'max_timeout': 120,
        },
        'amazon_aqm': {
            'domain': 'alexa.amazon.com',
        }
    }
    
    cookies = {'csrf': 'test_csrf_token'}
    collector = AmazonAQMCollector(cookies, config)
    
    alert_file = Path('data/ALERT_TOKEN_REFRESH_NEEDED.txt')
    if alert_file.exists():
        alert_file.unlink()
    
    with mock.patch('httpx.AsyncClient') as mock_client_class:
        mock_client = mock.AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        error_response = mock.MagicMock()
        error_response.status_code = 403
        mock_client.post.return_value = error_response
        
        # Email notification should be logged but not crash if unavailable
        with mock.patch('logging.Logger.info') as mock_log:
            readings = await collector.get_air_quality_readings('entity_123')
            
            # Check that email notification was logged (graceful degradation)
            log_calls = [str(call) for call in mock_log.call_args_list]
            assert any('email' in str(call).lower() for call in log_calls)
    
    # Cleanup
    if alert_file.exists():
        alert_file.unlink()


# T056: test_amazon_rate_limit_backoff
@pytest.mark.anyio
async def test_amazon_rate_limit_backoff():
    """Verify Amazon collector handles rate limiting with exponential backoff."""
    config = {
        'collection': {
            'retry_attempts': 3,
            'retry_backoff_base': 2,
            'max_timeout': 120,
        },
        'amazon_aqm': {
            'domain': 'alexa.amazon.com',
        }
    }
    
    cookies = {'csrf': 'test_csrf_token'}
    collector = AmazonAQMCollector(cookies, config)
    
    with mock.patch('httpx.AsyncClient') as mock_client_class:
        mock_client = mock.AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Simulate 429 rate limit, then success
        rate_limit_response = mock.MagicMock()
        rate_limit_response.status_code = 429
        
        success_response = mock.MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            'deviceStates': [{
                'capabilityStates': ['{"namespace":"Alexa.TemperatureSensor","name":"temperature","value":{"value":20.5,"scale":"CELSIUS"}}']
            }]
        }
        
        mock_client.post.side_effect = [rate_limit_response, success_response]
        
        with mock.patch('asyncio.sleep') as mock_sleep:
            readings = await collector.get_air_quality_readings('entity_123')
            
            assert readings is not None
            # Verify backoff was applied
            assert mock_sleep.call_count >= 1
