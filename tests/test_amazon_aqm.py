#!/usr/bin/env python3
"""
Unit tests for Amazon AQM Collector

Tests core functionality with mocked HTTP responses.
Covers device discovery, reading collection, and validation.
"""

import pytest
import asyncio
import json
import inspect
from unittest.mock import AsyncMock, MagicMock, patch
import pytest_asyncio

from source.collectors.amazon_collector import AmazonAQMCollector


class TestAmazonAQMCollectorInitialization:
    """Test collector initialization and configuration."""
    
    def test_init_with_cookies_and_config(self):
        """Test initialization with cookies and configuration."""
        cookies = {'session-id': 'test123', 'session-token': 'token123', 'csrf': 'csrf123'}
        config = {
            'amazon_aqm': {
                'domain': 'alexa.amazon.com',
                'timeout_seconds': 30
            },
            'collection': {
                'retry_attempts': 5,
                'retry_backoff_base': 2.0,
                'max_timeout': 120
            }
        }
        
        collector = AmazonAQMCollector(cookies=cookies, config=config)
        
        assert collector.cookies == cookies
        assert collector.domain == 'alexa.amazon.com'
        assert collector.retry_max_attempts == 5
        assert collector.retry_base_delay == 2.0
        assert collector.max_timeout == 120
    
    def test_init_with_default_config(self):
        """Test initialization with minimal config."""
        cookies = {'session-id': 'test123', 'session-token': 'token123', 'csrf': 'csrf123'}
        
        collector = AmazonAQMCollector(cookies=cookies)
        
        # Should use defaults
        assert collector.retry_max_attempts == 5
        assert collector.retry_base_delay == 1.0
        assert collector.domain == 'alexa.amazon.com'
        assert collector.max_timeout == 120


class TestDeviceDiscovery:
    """Test device discovery via GraphQL API."""
    
    @pytest.mark.asyncio
    async def test_list_devices_success(self):
        """Test successful device discovery."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        config = {}
        
        collector = AmazonAQMCollector(cookies=cookies, config=config)
        
        # Mock GraphQL response
        mock_response = {
            'data': {
                'endpoints': {
                    'items': [
                        {
                            'legacyAppliance': {
                                'applianceId': 'app123',
                                'friendlyName': 'Living Room AQM',
                                'friendlyDescription': 'Amazon Indoor Air Quality Monitor',
                                'applianceTypes': ['AIR_QUALITY_MONITOR'],
                                'entityId': 'entity123',
                                'capabilities': ['Alexa.TemperatureSensor'],
                                'alexaDeviceIdentifierList': [
                                    {'dmsDeviceSerialNumber': 'GAJ23005314600H3'}
                                ]
                            }
                        }
                    ]
                }
            }
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            # Set up mock to return async context manager
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                devices = await collector.list_devices()
        
        assert len(devices) == 1
        assert devices[0]['friendly_name'] == 'Living Room AQM'
        assert devices[0]['device_id'] == 'alexa:GAJ23005314600H3'
        assert devices[0]['device_serial'] == 'GAJ23005314600H3'
    
    @pytest.mark.asyncio
    async def test_list_devices_empty(self):
        """Test device discovery with no devices."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        config = {}
        
        collector = AmazonAQMCollector(cookies=cookies, config=config)
        
        mock_response = {
            'data': {
                'endpoints': {
                    'items': []
                }
            }
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                devices = await collector.list_devices()
        
        assert len(devices) == 0
    
    @pytest.mark.asyncio
    async def test_list_devices_api_error(self):
        """Test device discovery with API error."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        config = {'collection': {'retry_attempts': 1}}
        
        collector = AmazonAQMCollector(cookies=cookies, config=config)
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 500
            mock_response_obj.text = "Server Error"
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                devices = await collector.list_devices()
        
        assert len(devices) == 0


class TestReadingCollection:
    """Test air quality reading collection."""
    
    @pytest.mark.asyncio
    async def test_get_air_quality_readings_success(self):
        """Test successful reading collection."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        config = {}
        
        collector = AmazonAQMCollector(cookies=cookies, config=config)
        
        # Mock Phoenix State API response
        mock_response = {
            'deviceStates': [
                {
                    'capabilityStates': [
                        json.dumps({
                            'namespace': 'Alexa.TemperatureSensor',
                            'name': 'temperature',
                            'value': {'value': '22.5', 'scale': 'CELSIUS'}
                        }),
                        json.dumps({
                            'namespace': 'Alexa.RangeController',
                            'name': 'rangeValue',
                            'instance': '4',
                            'value': '45.0'
                        }),
                        json.dumps({
                            'namespace': 'Alexa.RangeController',
                            'name': 'rangeValue',
                            'instance': '6',
                            'value': '12.5'
                        })
                    ]
                }
            ]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                readings = await collector.get_air_quality_readings('entity123')
        
        assert readings is not None
        assert readings['temperature_celsius'] == 22.5
        assert readings['humidity_percent'] == 45.0
        assert readings['pm25_ugm3'] == 12.5
        assert 'timestamp' in readings
    
    @pytest.mark.asyncio
    async def test_get_air_quality_readings_api_error(self):
        """Test reading collection with API error."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        config = {'collection': {'retry_attempts': 1}}
        
        collector = AmazonAQMCollector(cookies=cookies, config=config)
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 401
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                readings = await collector.get_air_quality_readings('entity123')
        
        assert readings is None


class TestReadingValidation:
    """Test reading validation."""
    
    def test_validate_readings_all_valid(self):
        """Test validation of valid readings."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        collector = AmazonAQMCollector(cookies=cookies)
        
        readings = {
            'timestamp': '2024-01-01T00:00:00',
            'temperature_celsius': 22.5,
            'humidity_percent': 45.0,
            'pm25_ugm3': 12.5,
            'voc_ppb': 100.0,
            'co_ppm': 0.5,
            'iaq_score': 75
        }
        
        errors = collector.validate_readings(readings)
        assert len(errors) == 0
    
    def test_validate_readings_temperature_out_of_range(self):
        """Test validation with out-of-range temperature."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        collector = AmazonAQMCollector(cookies=cookies)
        
        readings = {
            'timestamp': '2024-01-01T00:00:00',
            'temperature_celsius': 45.0,  # Out of range (0-40)
            'humidity_percent': 45.0
        }
        
        errors = collector.validate_readings(readings)
        assert len(errors) == 1
        assert 'Temperature out of range' in errors[0]
    
    def test_validate_readings_humidity_out_of_range(self):
        """Test validation with invalid humidity."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        collector = AmazonAQMCollector(cookies=cookies)
        
        readings = {
            'timestamp': '2024-01-01T00:00:00',
            'temperature_celsius': 22.5,
            'humidity_percent': 105.0  # Out of range (0-100)
        }
        
        errors = collector.validate_readings(readings)
        assert len(errors) == 1
        assert 'Humidity out of range' in errors[0]
    
    def test_validate_readings_negative_values(self):
        """Test validation with negative sensor values."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        collector = AmazonAQMCollector(cookies=cookies)
        
        readings = {
            'timestamp': '2024-01-01T00:00:00',
            'temperature_celsius': 22.5,
            'humidity_percent': 45.0,
            'pm25_ugm3': -5.0,  # Invalid negative
            'voc_ppb': -10.0  # Invalid negative
        }
        
        errors = collector.validate_readings(readings)
        assert len(errors) == 2
        assert any('PM2.5' in e for e in errors)
        assert any('VOC' in e for e in errors)


class TestFormatReading:
    """Test reading formatting for database."""
    
    def test_format_reading_for_db(self):
        """Test formatting readings for database insertion."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        config = {
            'amazon_aqm': {
                'device_locations': {
                    'GAJ23005314600H3': 'Living Room'
                },
                'fallback_location': 'Unknown'
            }
        }
        
        collector = AmazonAQMCollector(cookies=cookies, config=config)
        
        readings = {
            'timestamp': '2024-01-01T12:00:00',
            'temperature_celsius': 22.5,
            'humidity_percent': 45.0,
            'pm25_ugm3': 12.5,
            'voc_ppb': 100.0
        }
        
        db_reading = collector.format_reading_for_db(
            entity_id='entity123',
            serial='GAJ23005314600H3',
            readings=readings,
            config=config
        )
        
        assert db_reading['device_id'] == 'alexa:GAJ23005314600H3'
        assert db_reading['location'] == 'Living Room'
        assert db_reading['device_type'] == 'alexa_aqm'
        assert db_reading['temperature_celsius'] == 22.5
        assert db_reading['humidity_percent'] == 45.0
        assert db_reading['pm25_ugm3'] == 12.5
    
    def test_format_reading_unknown_location(self):
        """Test formatting with unknown device location."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        config = {
            'amazon_aqm': {
                'device_locations': {},
                'fallback_location': 'Unknown'
            }
        }
        
        collector = AmazonAQMCollector(cookies=cookies, config=config)
        
        readings = {
            'timestamp': '2024-01-01T12:00:00',
            'temperature_celsius': 22.5
        }
        
        db_reading = collector.format_reading_for_db(
            entity_id='entity123',
            serial='GAJ_UNKNOWN',
            readings=readings,
            config=config
        )
        
        assert db_reading['location'] == 'Unknown'


class TestAsyncBehavior:
    """Test that async methods properly use await."""
    
    @pytest.mark.asyncio
    async def test_list_devices_is_async(self):
        """Verify list_devices is properly async."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        collector = AmazonAQMCollector(cookies=cookies)
        
        # Check that the method is a coroutine function
        assert inspect.iscoroutinefunction(collector.list_devices)
    
    @pytest.mark.asyncio
    async def test_get_readings_is_async(self):
        """Verify get_air_quality_readings is properly async."""
        cookies = {'session-id': 'test', 'session-token': 'token', 'csrf': 'csrf'}
        collector = AmazonAQMCollector(cookies=cookies)
        
        # Check that the method is a coroutine function
        assert inspect.iscoroutinefunction(collector.get_air_quality_readings)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
