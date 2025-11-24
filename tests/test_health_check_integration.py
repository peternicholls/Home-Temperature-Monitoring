"""
Tests for integrated health check with CLI interface.

Sprint: 005-system-reliability
Tasks: T078-T083 - Integration and CLI tests (TDD)
"""

import pytest
import sys
from io import StringIO
from unittest.mock import Mock, patch, MagicMock
from source.health_check import (
    HealthCheck,
    HealthStatus,
    run_health_check,
)


class TestHealthCheckAllPass:
    """Test health check when all components pass (T078)."""
    
    def test_health_check_all_pass_exit_0(self):
        """Test health check with all components passing returns exit code 0."""
        # Arrange
        validators = [
            Mock(return_value=(True, "Component A passed", None)),
            Mock(return_value=(True, "Component B passed", None)),
            Mock(return_value=(True, "Component C passed", None)),
        ]
        health_check = HealthCheck(validators=validators)
        
        # Act
        result = health_check.run()
        
        # Assert
        assert result.exit_code == 0
        assert result.overall_status == HealthStatus.PASS
        assert len(result.successes) == 3
        assert len(result.failures) == 0
    
    def test_health_check_all_pass_output_format(self):
        """Test health check output format when all pass."""
        # Arrange
        validators = [
            Mock(return_value=(True, "Database connection successful", None)),
        ]
        health_check = HealthCheck(validators=validators)
        
        # Act
        result = health_check.run()
        output = result.format_output()
        
        # Assert
        assert "HEALTH CHECK REPORT" in output
        assert "Overall Status: PASS" in output
        assert "✓ PASSED CHECKS:" in output
        assert "Database connection successful" in output
        assert "Exit Code: 0" in output


class TestHealthCheckPartialFailure:
    """Test health check with partial failures (T079)."""
    
    def test_health_check_partial_failure_exit_1(self):
        """Test health check with some failures returns exit code 1."""
        # Arrange
        validators = [
            Mock(return_value=(True, "Component A passed", None)),
            Mock(return_value=(False, "Component B failed", "Fix component B")),
            Mock(return_value=(True, "Component C passed", None)),
        ]
        health_check = HealthCheck(validators=validators)
        
        # Act
        result = health_check.run()
        
        # Assert
        assert result.exit_code == 1
        assert result.overall_status == HealthStatus.WARNING
        assert len(result.successes) == 2
        assert len(result.failures) == 1
    
    def test_health_check_partial_failure_remediation(self):
        """Test health check includes remediation guidance for failures."""
        # Arrange
        validators = [
            Mock(return_value=(False, "Log directory not writable", 
                             "Run: chmod 755 logs/")),
        ]
        health_check = HealthCheck(validators=validators)
        
        # Act
        result = health_check.run()
        output = result.format_output()
        
        # Assert
        assert "✗ FAILURES:" in output
        assert "Log directory not writable" in output


class TestHealthCheckCriticalFailure:
    """Test health check with critical failures (T080)."""
    
    def test_health_check_critical_failure_exit_2(self):
        """Test health check with critical failures returns exit code 2."""
        # Arrange
        critical_validator = Mock(return_value=(
            False, 
            "Database file corrupted", 
            "Restore from backup"
        ))
        critical_validator.critical = True
        
        validators = [
            Mock(return_value=(True, "Component A passed", None)),
            critical_validator,
        ]
        health_check = HealthCheck(validators=validators)
        
        # Act
        result = health_check.run()
        
        # Assert
        assert result.exit_code == 2
        assert result.overall_status == HealthStatus.CRITICAL
        assert len(result.failures) >= 1
    
    def test_health_check_multiple_critical_failures(self):
        """Test health check with multiple critical failures."""
        # Arrange
        critical_validator_1 = Mock(return_value=(
            False, "Database locked", "Restart database"
        ))
        critical_validator_1.critical = True
        
        critical_validator_2 = Mock(return_value=(
            False, "WAL mode disabled", "Enable WAL mode"
        ))
        critical_validator_2.critical = True
        
        validators = [critical_validator_1, critical_validator_2]
        health_check = HealthCheck(validators=validators)
        
        # Act
        result = health_check.run()
        
        # Assert
        assert result.exit_code == 2
        assert result.overall_status == HealthStatus.CRITICAL


class TestHealthCheckTimeoutEnforcement:
    """Test health check timeout enforcement (T081)."""
    
    def test_health_check_timeout_enforcement(self):
        """Test health check enforces 15 second timeout."""
        import time
        
        # Arrange - create slow validator
        def slow_validator():
            time.sleep(2)
            return (True, "Slow component", None)
        
        validators = [slow_validator] * 10  # Would take 20 seconds total
        health_check = HealthCheck(validators=validators, timeout=2)
        
        # Act
        start_time = time.time()
        result = health_check.run()
        elapsed = time.time() - start_time
        
        # Assert - should stop before all validators complete
        assert elapsed < 5  # Allow some overhead, but much less than 20s
        assert len(result.successes) + len(result.failures) < 10
    
    def test_health_check_timeout_logs_failure(self):
        """Test health check logs timeout as critical failure."""
        import time
        
        # Arrange
        def slow_validator():
            time.sleep(5)
            return (True, "Never completes", None)
        
        validators = [slow_validator]
        health_check = HealthCheck(validators=validators, timeout=1)
        
        # Act
        result = health_check.run()
        
        # Assert
        # Timeout should result in some failure indication
        assert result.exit_code != 0 or len(result.failures) > 0


class TestHealthCheckOutputFormat:
    """Test health check output format (T082)."""
    
    def test_health_check_output_format_complete(self):
        """Test health check output includes all required sections."""
        # Arrange
        validators = [
            Mock(return_value=(True, "Component A passed", None)),
            Mock(return_value=(False, "Component B failed", "Fix B")),
        ]
        health_check = HealthCheck(validators=validators)
        
        # Act
        result = health_check.run()
        output = result.format_output()
        
        # Assert
        assert "HEALTH CHECK REPORT" in output
        assert "Overall Status:" in output
        assert "✓ PASSED CHECKS:" in output
        assert "✗ FAILURES:" in output
        assert "Exit Code:" in output
        assert "=" in output  # Separator lines
    
    def test_health_check_output_no_credential_leak(self):
        """Test health check output never contains credentials."""
        # Arrange
        validators = [
            Mock(return_value=(
                False, 
                "Auth failed for secret: HIDDEN_CREDENTIAL_12345",
                "Refresh credentials"
            )),
        ]
        health_check = HealthCheck(validators=validators)
        
        # Act
        result = health_check.run()
        output = result.format_output()
        
        # Assert
        # Output sanitization should remove long credential-like strings
        assert "HIDDEN_CREDENTIAL_12345" not in output or "[REDACTED]" in output


class TestHealthCheckRemediationGuidance:
    """Test health check remediation guidance (T083)."""
    
    def test_health_check_provides_remediation(self):
        """Test health check includes remediation guidance for all failures."""
        # Arrange
        validators = [
            Mock(return_value=(
                False, 
                "Hue Bridge unreachable",
                "Check Hue Bridge IP address in config.yaml and network connectivity"
            )),
            Mock(return_value=(
                False,
                "Database not writable",
                "Run: chmod 644 data/temperature_readings.db"
            )),
        ]
        health_check = HealthCheck(validators=validators)
        
        # Act
        result = health_check.run()
        output = result.format_output()
        
        # Assert
        assert "Hue Bridge unreachable" in output
        assert "Database not writable" in output
        # Remediation is in the failure message
        assert "config.yaml" in output or "chmod" in output
    
    def test_health_check_actionable_diagnostics(self):
        """Test health check provides actionable error diagnostics."""
        # Arrange
        validators = [
            Mock(return_value=(
                False,
                "Amazon AQM credentials expired",
                "Run: python source/collectors/amazon_auth.py to refresh OAuth tokens"
            )),
        ]
        health_check = HealthCheck(validators=validators)
        
        # Act
        result = health_check.run()
        
        # Assert
        assert len(result.failures) == 1
        assert "credentials expired" in result.failures[0].lower()


class TestHealthCheckCLI:
    """Test health check CLI entry point."""
    
    @patch('source.health_check.HealthCheck')
    def test_run_health_check_cli_returns_exit_code(self, mock_health_check):
        """Test run_health_check CLI returns correct exit code."""
        # Arrange
        mock_instance = mock_health_check.return_value
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.format_output.return_value = "Health check passed"
        mock_instance.run.return_value = mock_result
        
        # Act
        with patch('builtins.print'):
            exit_code = run_health_check()
        
        # Assert
        assert exit_code == 0
    
    @patch('source.health_check.HealthCheck')
    def test_run_health_check_cli_prints_output(self, mock_health_check):
        """Test run_health_check CLI prints formatted output."""
        # Arrange
        mock_instance = mock_health_check.return_value
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.format_output.return_value = "Formatted health check output"
        mock_instance.run.return_value = mock_result
        
        # Act
        with patch('builtins.print') as mock_print:
            run_health_check()
        
        # Assert
        mock_print.assert_called_once_with("Formatted health check output")
