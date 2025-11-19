import pytest
from unittest.mock import MagicMock, patch
from source.collectors import hue_collector

# Sample config and sensor data for tests
def sample_config():
    return {
        'collectors': {
            'hue': {
                'temperature_min': 0.0,
                'temperature_max': 40.0,
                'sensor_locations': {'uniqueid1': 'Living Room'},
                'fallback_to_name': True,
                'retry_attempts': 2,
                'retry_backoff_base': 1,
            }
        },
        'storage': {
            'database_path': 'data/test_readings.db'
        }
    }

def sample_sensor_data():
    return {
        'uniqueid': 'uniqueid1',
        'name': 'Test Sensor',
        'type': 'ZLLTemperature',
        'config': {'reachable': True, 'battery': 90},
        'state': {'temperature': 2150, 'lastupdated': '2025-11-19T12:00:00'},
        'modelid': 'ModelX',
        'manufacturername': 'Philips',
    }

@patch('source.collectors.hue_collector.requests.get')
def test_discover_sensors(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {'1': sample_sensor_data()}
    mock_response.text = str(mock_response.json.return_value)
    mock_get.return_value = mock_response
    mock_get.return_value.raise_for_status = lambda: None

    bridge = MagicMock()
    bridge.username = 'api_key'
    bridge.ip = '1.2.3.4'
    config = sample_config()

    sensors = hue_collector.discover_sensors(bridge, config)
    assert len(sensors) == 1
    assert sensors[0]['location'] == 'Living Room'
    assert sensors[0]['is_reachable'] is True
    assert sensors[0]['battery_level'] == 90

@patch('source.collectors.hue_collector.requests.get')
def test_collect_reading_from_sensor(mock_get):
    mock_response = MagicMock()
    sensor_data = sample_sensor_data()
    mock_response.json.return_value = sensor_data
    mock_response.text = str(sensor_data)
    mock_get.return_value = mock_response
    mock_get.return_value.raise_for_status = lambda: None

    bridge = MagicMock()
    bridge.username = 'api_key'
    bridge.ip = '1.2.3.4'
    config = sample_config()
    
    sensor_info = {
        'unique_id': 'uniqueid1',
        'location': 'Living Room',
        'sensor_id': '1'
    }
    
    # Use the actual function signature with cached data
    cached_data = {'1': sensor_data}
    reading = hue_collector.collect_reading_from_sensor(bridge, '1', sensor_info, config, cached_data)
    
    assert reading is not None
    assert reading['temperature_celsius'] == 21.5
    assert reading['location'] == 'Living Room'
    assert reading['battery_level'] == 90

@patch('source.collectors.hue_collector.discover_sensors')
@patch('source.collectors.hue_collector.requests.get')
def test_collect_all_readings(mock_get, mock_discover):
    # Mock the sensors API call for caching
    mock_response = MagicMock()
    sensor_data = sample_sensor_data()
    mock_response.json.return_value = {'1': sensor_data}
    mock_response.text = str(sensor_data)
    mock_get.return_value = mock_response
    mock_get.return_value.raise_for_status = lambda: None
    
    mock_discover.return_value = [
        {
            'sensor_id': '1',
            'unique_id': 'uniqueid1',
            'name': 'Test Sensor',
            'model_id': 'ModelX',
            'manufacturer': 'Philips',
            'sensor_type': 'ZLLTemperature',
            'location': 'Living Room',
            'is_reachable': True,
            'battery_level': 90,
            'last_updated': '2025-11-19T12:00:00',
        }
    ]
    bridge = MagicMock()
    bridge.username = 'api_key'
    bridge.ip = '1.2.3.4'
    config = sample_config()
    
    readings = hue_collector.collect_all_readings(bridge, config)
    assert len(readings) == 1
    assert readings[0]['location'] == 'Living Room'
    assert readings[0]['temperature_celsius'] == 21.5
    assert readings[0]['battery_level'] == 90
