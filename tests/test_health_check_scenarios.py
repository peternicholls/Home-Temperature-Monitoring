"""
Integration tests for health check validation suite.
Sprint: 005-system-reliability
Phase: 8
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from source.health_check import (
    validate_configuration,
    validate_secrets,
    validate_database_write,
    validate_log_rotation_config,
    validate_hue_bridge_connectivity,
    validate_amazon_aqm_connectivity,
    validate_wal_mode,
    HealthCheck,
    HealthStatus
)

class TestHealthCheckScenarios:
    """Test health check against various failure scenarios."""

    def test_missing_config_yaml(self):
        """T113: Test health check against missing config.yaml."""
        with patch('source.config.loader.ConfigLoader') as MockLoader:
            mock_loader = MockLoader.return_value
            # Simulate missing required params
            mock_loader.config = {}
            
            passed, message, remediation = validate_configuration()
            
            assert passed is False
            assert "missing required parameters" in message
            assert remediation is not None

    def test_invalid_secrets_yaml(self):
        """T114: Test health check against invalid secrets.yaml format."""
        with patch('source.config.loader.ConfigLoader') as MockLoader:
            mock_loader = MockLoader.return_value
            # Simulate invalid secrets (missing required keys)
            mock_loader.secrets = {}
            
            passed, message, remediation = validate_secrets()
            
            assert passed is False
            assert "Secrets missing" in message
            assert remediation is not None

    def test_missing_hue_username(self):
        """T115: Test health check against missing Hue Bridge username."""
        with patch('source.config.loader.ConfigLoader') as MockLoader:
            mock_loader = MockLoader.return_value
            # Simulate missing hue username
            mock_loader.secrets = {
                'amazon_client_id': 'amzn1.application.test',
                'amazon_client_secret': 'test_secret'
            }
            
            # This should pass overall secrets validation if Amazon is present,
            # but we want to test specific Hue validation if possible.
            # validate_secrets checks if EITHER is present.
            
            # Let's check validate_hue_bridge_connectivity
            with patch('source.collectors.hue_collector.connect_to_bridge') as mock_connect:
                mock_connect.side_effect = PermissionError("Unauthorized")
                
                passed, message, remediation = validate_hue_bridge_connectivity()
                
                assert passed is False
                assert "authentication failed" in message

    def test_missing_amazon_credentials(self):
        """T116: Test health check against missing Amazon credentials."""
        with patch('source.config.loader.ConfigLoader') as MockLoader:
            mock_loader = MockLoader.return_value
            mock_loader.secrets = {'hue_bridge_username': 'valid_username'}
            
            passed, message, remediation = validate_amazon_aqm_connectivity()
            
            assert passed is False
            assert "not configured" in message

    def test_read_only_database(self):
        """T117: Test health check against read-only database file."""
        with patch('source.storage.manager.StorageManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.test_write_with_rollback.return_value = False
            
            passed, message, remediation = validate_database_write()
            
            assert passed is False
            assert "failed" in message

    def test_non_writable_log_directory(self):
        """T118: Test health check against non-writable log directory."""
        with patch('source.config.loader.ConfigLoader') as MockLoader:
            mock_loader = MockLoader.return_value
            mock_loader.config = {
                'log_directory': '/logs',
                'log_rotation_threshold_mb': 10,
                'log_backup_count': 5
            }
            
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_dir', return_value=True):
                    with patch('os.access', return_value=False):
                        passed, message, remediation = validate_log_rotation_config()
                        
                        assert passed is False
                        assert "not writable" in message

    def test_wal_mode_disabled(self):
        """T119: Test health check against WAL mode disabled."""
        with patch('source.storage.manager.StorageManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.verify_wal_mode.return_value = False
            
            passed, message, remediation = validate_wal_mode()
            
            assert passed is False
            assert "not enabled" in message

    def test_unreachable_hue_bridge(self):
        """T120: Test health check against unreachable Hue Bridge."""
        with patch('source.collectors.hue_collector.connect_to_bridge') as mock_connect:
            mock_connect.side_effect = ConnectionError("Unreachable")
            
            passed, message, remediation = validate_hue_bridge_connectivity()
            
            assert passed is False
            assert "unreachable" in message

    def test_invalid_amazon_credentials(self):
        """T121: Test health check against invalid Amazon AQM credentials."""
        with patch('source.config.loader.ConfigLoader') as MockLoader:
            mock_loader = MockLoader.return_value
            mock_loader.secrets = {
                'amazon': {
                    'client_id': 'invalid_format',
                    'client_secret': 'secret'
                }
            }
            
            passed, message, remediation = validate_amazon_aqm_connectivity()
            
            assert passed is False
            assert "invalid format" in message

    def test_multiple_simultaneous_failures(self):
        """T122: Test health check against multiple simultaneous failures."""
        # Mock multiple validators to fail
        mock_val1 = Mock(return_value=(False, "Fail 1", "Fix 1"))
        mock_val2 = Mock(return_value=(False, "Fail 2", "Fix 2"))
        mock_val3 = Mock(return_value=(True, "Pass 3", None))
        
        hc = HealthCheck(validators=[mock_val1, mock_val2, mock_val3])
        result = hc.run()
        
        assert result.overall_status == HealthStatus.WARNING
        assert len(result.failures) == 2
        assert len(result.successes) == 1
        assert result.exit_code == 1

