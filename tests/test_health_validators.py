"""
Tests for individual health check component validators.

Sprint: 005-system-reliability
Tasks: T070-T077 - Component validator tests (TDD)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from source.health_check import (
    validate_wal_mode,
    validate_configuration,
    validate_secrets,
    validate_database_write,
    validate_log_rotation_config,
    validate_hue_bridge_connectivity,
    validate_amazon_aqm_connectivity,
)


class TestWALModeValidation:
    """Test WAL mode validator (T070)."""
    
    @patch('source.storage.manager.StorageManager')
    def test_validate_wal_mode_enabled(self, mock_storage):
        """Test WAL mode validation when enabled."""
        # Arrange
        mock_instance = mock_storage.return_value
        mock_instance.verify_wal_mode.return_value = True
        mock_instance.get_wal_checkpoint_interval.return_value = 1000
        
        # Act
        passed, message, remediation = validate_wal_mode()
        
        # Assert
        assert passed is True
        assert "WAL mode enabled" in message
        assert remediation is None
    
    @patch('source.storage.manager.StorageManager')
    def test_validate_wal_mode_disabled(self, mock_storage):
        """Test WAL mode validation when disabled."""
        # Arrange
        mock_instance = mock_storage.return_value
        mock_instance.verify_wal_mode.return_value = False
        
        # Act
        passed, message, remediation = validate_wal_mode()
        
        # Assert
        assert passed is False
        assert "WAL mode" in message.lower()
        assert "Enable WAL mode" in remediation


class TestConfigurationValidation:
    """Test configuration validator (T071)."""
    
    @patch('source.config.loader.ConfigLoader')
    def test_validate_configuration_valid(self, mock_loader):
        """Test configuration validation when all required parameters present."""
        # Arrange
        mock_instance = mock_loader.return_value
        mock_instance.config = {
            'collection_interval': 300,
            'database_path': 'data/temperature_readings.db',
            'log_level': 'INFO',
            'hue_bridge_ip': '192.168.1.100'
        }
        
        # Act
        passed, message, remediation = validate_configuration()
        
        # Assert
        assert passed is True
        assert "Configuration valid" in message
    
    @patch('source.config.loader.ConfigLoader')
    def test_validate_configuration_missing_parameters(self, mock_loader):
        """Test configuration validation when parameters missing."""
        # Arrange
        mock_instance = mock_loader.return_value
        mock_instance.config = {'collection_interval': 300}
        
        # Act
        passed, message, remediation = validate_configuration()
        
        # Assert
        assert passed is False
        assert "missing" in message.lower()
        assert "config.yaml" in remediation.lower()
    
    @patch('source.config.loader.ConfigLoader')
    def test_validate_configuration_invalid_ranges(self, mock_loader):
        """Test configuration validation when values out of range."""
        # Arrange
        mock_instance = mock_loader.return_value
        mock_instance.config = {
            'collection_interval': -100,  # Invalid negative
            'database_path': 'data/temperature_readings.db',
            'log_level': 'INFO'
        }
        
        # Act
        passed, message, remediation = validate_configuration()
        
        # Assert
        assert passed is False
        assert "range" in message.lower() or "invalid" in message.lower()


class TestSecretsValidation:
    """Test secrets validator (T072)."""
    
    @patch('source.config.loader.ConfigLoader')
    def test_validate_secrets_present(self, mock_loader):
        """Test secrets validation when all required secrets present."""
        # Arrange
        mock_instance = mock_loader.return_value
        mock_instance.secrets = {
            'hue': {
                'api_key': 'test_username_12345'
            }
        }
        
        # Act
        passed, message, remediation = validate_secrets()
        
        # Assert
        assert passed is True
        assert "Secrets validated" in message
        # Ensure no credential leakage
        assert "test_username" not in message
    
    @patch('source.config.loader.ConfigLoader')
    def test_validate_secrets_missing(self, mock_loader):
        """Test secrets validation when secrets missing."""
        # Arrange
        mock_instance = mock_loader.return_value
        mock_instance.secrets = {}
        
        # Act
        passed, message, remediation = validate_secrets()
        
        # Assert
        assert passed is False
        assert "missing" in message.lower()
        assert "secrets.yaml" in remediation.lower()
    
    @patch('source.config.loader.ConfigLoader')
    def test_validate_secrets_invalid_format(self, mock_loader):
        """Test secrets validation when format incorrect."""
        # Arrange
        mock_instance = mock_loader.return_value
        mock_instance.secrets = {
            'hue': {
                'api_key': 'short'  # Too short
            }
        }
        
        # Act
        passed, message, remediation = validate_secrets()
        
        # Assert
        assert passed is False
        assert "invalid" in message.lower() or "format" in message.lower()
    
    def test_validate_secrets_no_credential_leak(self):
        """Test secrets validator never leaks credentials (T077)."""
        # Arrange
        with patch('source.config.loader.ConfigLoader') as mock_loader:
            mock_instance = mock_loader.return_value
            mock_instance.secrets = {
                'hue': {
                    'api_key': 'SENSITIVE_USERNAME_12345'
                }
            }
            
            # Act
            passed, message, remediation = validate_secrets()
            
            # Assert - no actual credentials in output
            assert "SENSITIVE_USERNAME" not in message
            if remediation:
                assert "SENSITIVE_USERNAME" not in remediation


class TestDatabaseWriteValidation:
    """Test database write validator (T073)."""
    
    @patch('source.storage.manager.StorageManager')
    def test_validate_database_write_success(self, mock_storage):
        """Test database write validation when successful."""
        # Arrange
        mock_instance = mock_storage.return_value
        mock_instance.test_write_with_rollback.return_value = True
        
        # Act
        passed, message, remediation = validate_database_write()
        
        # Assert
        assert passed is True
        assert "Database writable" in message
        mock_instance.test_write_with_rollback.assert_called_once()
    
    @patch('source.storage.manager.StorageManager')
    def test_validate_database_write_failure(self, mock_storage):
        """Test database write validation when write fails."""
        # Arrange
        mock_instance = mock_storage.return_value
        mock_instance.test_write_with_rollback.side_effect = PermissionError("Read-only")
        
        # Act
        passed, message, remediation = validate_database_write()
        
        # Assert
        assert passed is False
        assert "write" in message.lower() or "permission" in message.lower()
        assert "permissions" in remediation.lower()
    
    @patch('source.storage.manager.StorageManager')
    def test_validate_database_write_rollback(self, mock_storage):
        """Test database write validation performs rollback."""
        # Arrange
        mock_instance = mock_storage.return_value
        mock_instance.test_write_with_rollback.return_value = True
        
        # Act
        validate_database_write()
        
        # Assert - verify rollback was called
        mock_instance.test_write_with_rollback.assert_called_once()


class TestLogRotationConfigValidation:
    """Test log rotation config validator (T074)."""
    
    @patch('source.health_check.Path')
    @patch('source.config.loader.ConfigLoader')
    def test_validate_log_rotation_config_valid(self, mock_loader, mock_path):
        """Test log rotation config validation when valid."""
        # Arrange
        mock_instance = mock_loader.return_value
        mock_instance.config = {
            'log_directory': 'logs/',
            'log_rotation_threshold_mb': 10,
            'log_backup_count': 5
        }
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.is_dir.return_value = True
        
        with patch('os.access', return_value=True):
            # Act
            passed, message, remediation = validate_log_rotation_config()
            
            # Assert
            assert passed is True
            assert "Log rotation configured" in message
    
    @patch('source.health_check.Path')
    def test_validate_log_rotation_config_directory_missing(self, mock_path):
        """Test log rotation config validation when directory missing."""
        # Arrange
        mock_path.return_value.exists.return_value = False
        
        # Act
        passed, message, remediation = validate_log_rotation_config()
        
        # Assert
        assert passed is False
        assert "directory" in message.lower()
        assert "mkdir" in remediation.lower() or "create" in remediation.lower()
    
    @patch('source.health_check.Path')
    @patch('source.config.loader.ConfigLoader')
    def test_validate_log_rotation_config_not_writable(self, mock_loader, mock_path):
        """Test log rotation config validation when directory not writable."""
        # Arrange
        mock_instance = mock_loader.return_value
        mock_instance.config = {'log_directory': 'logs/'}
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.is_dir.return_value = True
        
        with patch('os.access', return_value=False):
            # Act
            passed, message, remediation = validate_log_rotation_config()
            
            # Assert
            assert passed is False
            assert "writable" in message.lower() or "permission" in message.lower()


class TestHueBridgeConnectivityValidation:
    """Test Hue Bridge connectivity validator (T075)."""
    
    @patch('source.collectors.hue_collector.discover_sensors')
    @patch('source.collectors.hue_collector.connect_to_bridge')
    @patch('source.config.loader.ConfigLoader')
    def test_validate_hue_bridge_connectivity_success(self, mock_loader, mock_connect, mock_discover):
        """Test Hue Bridge connectivity validation when successful."""
        # Arrange
        mock_loader.return_value.config = {}
        mock_loader.return_value.secrets = {}
        mock_bridge = Mock()
        mock_connect.return_value = mock_bridge
        mock_discover.return_value = [{'id': '1', 'name': 'Sensor 1'}]
        
        # Act
        passed, message, remediation = validate_hue_bridge_connectivity()
        
        # Assert
        assert passed is True
        assert "Hue Bridge reachable" in message
    
    @patch('source.collectors.hue_collector.connect_to_bridge')
    @patch('source.config.loader.ConfigLoader')
    def test_validate_hue_bridge_connectivity_unreachable(self, mock_loader, mock_connect):
        """Test Hue Bridge connectivity validation when unreachable."""
        # Arrange
        mock_loader.return_value.config = {}
        mock_loader.return_value.secrets = {}
        mock_connect.side_effect = ConnectionError("Bridge unreachable")
        
        # Act
        passed, message, remediation = validate_hue_bridge_connectivity()
        
        # Assert
        assert passed is False
        assert "unreachable" in message.lower() or "connection" in message.lower()
        assert "IP address" in remediation or "network" in remediation
    
    @patch('source.collectors.hue_collector.connect_to_bridge')
    @patch('source.config.loader.ConfigLoader')
    def test_validate_hue_bridge_connectivity_auth_failure(self, mock_loader, mock_connect):
        """Test Hue Bridge connectivity validation when auth fails."""
        # Arrange
        mock_loader.return_value.config = {}
        mock_loader.return_value.secrets = {}
        mock_connect.side_effect = PermissionError("Unauthorized")
        
        # Act
        passed, message, remediation = validate_hue_bridge_connectivity()
        
        # Assert
        assert passed is False
        assert "auth" in message.lower() or "unauthorized" in message.lower() or "permission" in message.lower()
        assert "authentication" in remediation.lower() or "auth" in remediation.lower()


class TestAmazonAQMConnectivityValidation:
    """Test Amazon AQM connectivity validator (T076)."""
    
    @patch('source.config.loader.ConfigLoader')
    def test_validate_amazon_aqm_connectivity_success(self, mock_loader):
        """Test Amazon AQM connectivity validation when successful."""
        # Arrange
        mock_loader.return_value.config = {}
        mock_loader.return_value.secrets = {
            'amazon': {
                'client_id': 'amzn1.test.id',
                'client_secret': 'test_secret'
            }
        }
        
        # Act
        passed, message, remediation = validate_amazon_aqm_connectivity()
        
        # Assert
        assert passed is True
        assert "Amazon AQM" in message
    
    @patch('source.config.loader.ConfigLoader')
    def test_validate_amazon_aqm_connectivity_network_failure(self, mock_loader):
        """Test Amazon AQM connectivity validation when network fails."""
        # Arrange
        mock_loader.return_value.config = {}
        mock_loader.return_value.secrets = {}
        
        # Act
        passed, message, remediation = validate_amazon_aqm_connectivity()
        
        # Assert
        assert passed is False
        assert "not configured" in message.lower() or "missing" in message.lower()
    
    @patch('source.config.loader.ConfigLoader')
    def test_validate_amazon_aqm_connectivity_invalid_credentials(self, mock_loader):
        """Test Amazon AQM connectivity validation when credentials invalid."""
        # Arrange
        mock_loader.return_value.config = {}
        mock_loader.return_value.secrets = {
            'amazon': {
                'client_id': 'invalid_format',  # doesn't start with 'amzn'
                'client_secret': 'test'
            }
        }
        
        # Act
        passed, message, remediation = validate_amazon_aqm_connectivity()
        
        # Assert
        assert passed is False
        assert "invalid" in message.lower() or "format" in message.lower()
        assert "credentials" in remediation.lower() or "Amazon" in remediation
