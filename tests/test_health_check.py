"""
Test suite for health check framework.

Following TDD: These tests are written BEFORE implementation and MUST FAIL initially.
Sprint: 005-system-reliability
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from source.health_check import (
    HealthCheck,
    ComponentValidator,
    HealthStatus,
    run_health_check
)


class TestHealthCheck:
    """Test health check framework functionality."""

    def test_health_check_all_pass(self):
        """Test health check when all components pass."""
        mock_validators = [
            Mock(name="validator1", return_value=(True, "OK", None)),
            Mock(name="validator2", return_value=(True, "OK", None)),
            Mock(name="validator3", return_value=(True, "OK", None))
        ]
        
        health_check = HealthCheck(validators=mock_validators)
        status = health_check.run()
        
        assert status.overall_status == HealthStatus.PASS
        assert status.exit_code == 0
        assert len(status.failures) == 0

    def test_health_check_partial_failure(self):
        """Test health check with some component failures."""
        mock_validators = [
            Mock(name="validator1", return_value=(True, "OK", None)),
            Mock(name="validator2", return_value=(False, "Config missing", "Check config.yaml")),
            Mock(name="validator3", return_value=(True, "OK", None))
        ]
        
        health_check = HealthCheck(validators=mock_validators)
        status = health_check.run()
        
        assert status.overall_status == HealthStatus.WARNING
        assert status.exit_code == 1
        assert len(status.failures) == 1
        assert "Config missing" in status.failures[0]

    def test_health_check_critical_failure(self):
        """Test health check with critical component failure."""
        mock_validators = [
            Mock(name="database", return_value=(False, "Database unreachable", "Check database file"), critical=True),
            Mock(name="validator2", return_value=(True, "OK", None))
        ]
        
        health_check = HealthCheck(validators=mock_validators)
        status = health_check.run()
        
        assert status.overall_status == HealthStatus.CRITICAL
        assert status.exit_code == 2
        assert len(status.failures) >= 1

    def test_health_check_timeout(self):
        """Test health check enforces timeout."""
        def slow_validator():
            import time
            time.sleep(20)  # Exceeds 15-second limit
            return (True, "OK", None)
        
        mock_validators = [slow_validator]
        
        health_check = HealthCheck(validators=mock_validators, timeout=1)
        
        import time
        start = time.time()
        status = health_check.run()
        elapsed = time.time() - start
        
        # Should timeout and not wait full 20 seconds
        assert elapsed < 2
        assert status.overall_status != HealthStatus.PASS

    def test_health_check_security_no_credential_leak(self):
        """Test health check output doesn't leak credentials."""
        secrets = {
            "hue_username": "secret_api_key_12345",
            "amazon_refresh_token": "very_secret_token_xyz"
        }
        
        mock_validators = [
            Mock(name="secrets", return_value=(False, "Invalid credentials", "Regenerate API key"))
        ]
        
        health_check = HealthCheck(validators=mock_validators)
        status = health_check.run()
        output = status.format_output()
        
        # Ensure no secrets appear in output
        assert "secret_api_key" not in output
        assert "very_secret_token" not in output
        assert "credentials" in output.lower()  # Generic message OK

    def test_health_check_exit_codes(self):
        """Test correct exit codes for different scenarios."""
        # All pass -> 0
        health_check_pass = HealthCheck(validators=[
            Mock(return_value=(True, "OK", None))
        ])
        assert health_check_pass.run().exit_code == 0
        
        # Some fail -> 1
        health_check_warn = HealthCheck(validators=[
            Mock(return_value=(True, "OK", None)),
            Mock(return_value=(False, "Warning", "Fix it"))
        ])
        assert health_check_warn.run().exit_code == 1
        
        # Critical fail -> 2
        health_check_critical = HealthCheck(validators=[
            Mock(return_value=(False, "Critical error", "Fix now"), critical=True)
        ])
        assert health_check_critical.run().exit_code == 2

    def test_health_check_component_isolation(self):
        """Test component failures don't prevent other checks."""
        call_order = []
        
        def validator1():
            call_order.append("v1")
            raise Exception("Validator 1 crashed")
        
        def validator2():
            call_order.append("v2")
            return (True, "OK", None)
        
        def validator3():
            call_order.append("v3")
            return (True, "OK", None)
        
        health_check = HealthCheck(validators=[validator1, validator2, validator3])
        status = health_check.run()
        
        # All validators should run despite v1 crashing
        assert "v1" in call_order
        assert "v2" in call_order
        assert "v3" in call_order
        assert len(call_order) == 3
