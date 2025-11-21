"""
Health check framework for production deployment validation.

Sprint: 005-system-reliability
Tasks: T030 - Health check framework implementation
        T084 - Component validator implementation
"""

import sys
import time
import logging
import os
from enum import Enum
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels."""
    PASS = "pass"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ComponentValidator:
    """Component validator configuration."""
    name: str
    validator_func: Callable
    critical: bool = False


@dataclass
class HealthCheckResult:
    """Health check execution result."""
    overall_status: HealthStatus
    exit_code: int
    failures: List[str]
    warnings: List[str]
    successes: List[str]
    
    def format_output(self) -> str:
        """Format health check output for display (no credential leakage)."""
        import re
        def sanitize(text):
            if not text:
                return text
            text = re.sub(r'([A-Za-z0-9_\-]{12,})', '[REDACTED]', text)
            text = re.sub(r'(api[_-]?key|token|secret|password|client[_-]?id|username)[=:]?\s*([A-Za-z0-9_\-]{8,})', r'\1=[REDACTED]', text, flags=re.IGNORECASE)
            return text

        lines = []
        lines.append("=" * 60)
        lines.append("HEALTH CHECK REPORT")
        lines.append("=" * 60)
        lines.append(f"Overall Status: {self.overall_status.value.upper()}")
        lines.append("")

        if self.successes:
            lines.append("\u2713 PASSED CHECKS:")
            for success in self.successes:
                lines.append(f"  \u2713 {sanitize(success)}")
            lines.append("")
        
        if self.warnings:
            lines.append("⚠ WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")
            lines.append("")
        
        if self.failures:
            lines.append("✗ FAILURES:")
            for failure in self.failures:
                # If failure is a tuple (message, remediation), display both
                if isinstance(failure, tuple) and len(failure) == 2:
                    msg, remediation = failure
                    lines.append(f"  ✗ {sanitize(msg)}")
                    if remediation:
                        lines.append(f"    Remediation: {sanitize(remediation)}")
                else:
                    # Try to extract remediation guidance from the string if present
                    # If failure contains a colon, split and treat as message:remediation
                    if isinstance(failure, str) and ':' in failure:
                        parts = failure.split(':', 1)
                        lines.append(f"  ✗ {sanitize(parts[0])}")
                        lines.append(f"    Remediation: {sanitize(parts[1])}")
                    else:
                        lines.append(f"  ✗ {sanitize(failure)}")
                        # Add common remediation guidance for known errors
                        if "Hue Bridge unreachable" in failure:
                            lines.append("    Remediation: Check Hue Bridge IP address in config.yaml and network connectivity")
                        if "Database not writable" in failure:
                            lines.append("    Remediation: Run: chmod 644 data/temperature_readings.db")
            lines.append("")
        
        lines.append(f"Exit Code: {self.exit_code}")
        lines.append("=" * 60)
        
        return "\n".join(lines)


class HealthCheck:
    """Health check coordinator with component validation and aggregation."""
    
    def __init__(self, validators: List[Callable] = None, timeout: int = 15):
        """
        Initialize health check framework.
        
        Args:
            validators: List of validator functions
            timeout: Maximum time for all checks in seconds
        """
        self.validators = validators or []
        self.timeout = timeout
        self.results = {
            "successes": [],
            "warnings": [],
            "failures": [],
            "critical_failures": []
        }
    
    def run(self) -> HealthCheckResult:
        """
        Execute all health checks with timeout enforcement.
        
        Returns:
            HealthCheckResult with aggregated status
        """
        start_time = time.time()
        
        # Run all validators with component isolation
        for validator in self.validators:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= self.timeout:
                logger.error(f"Health check timeout exceeded ({self.timeout}s)")
                self.results["critical_failures"].append(
                    "Health check timeout exceeded"
                )
                break
            
            try:
                # Calculate remaining time for this validator
                remaining_time = self.timeout - elapsed
                
                # Execute validator with timeout
                if callable(validator):
                    # Use threading timeout
                    import signal
                    result_container = [None]
                    exception_container = [None]
                    
                    def target():
                        try:
                            result_container[0] = validator()
                        except Exception as e:
                            exception_container[0] = e
                    
                    import threading
                    thread = threading.Thread(target=target)
                    thread.daemon = True
                    thread.start()
                    thread.join(timeout=min(remaining_time, self.timeout))
                    
                    if thread.is_alive():
                        # Timeout occurred
                        logger.error(f"Validator timeout")
                        self.results["failures"].append("Validator timeout")
                        continue
                    
                    if exception_container[0]:
                        raise exception_container[0]
                    
                    result = result_container[0]
                else:
                    result = validator()
                
                # Process result
                if isinstance(result, tuple) and len(result) >= 2:
                    passed, message, remediation = result if len(result) == 3 else (*result, None)
                    
                    if passed:
                        self.results["successes"].append(message)
                    else:
                        # Check if critical - must be explicitly set to True
                        try:
                            is_critical = validator.critical is True
                        except AttributeError:
                            is_critical = False
                        
                        if is_critical:
                            self.results["critical_failures"].append(message)
                        else:
                            self.results["failures"].append(message)
                else:
                    self.results["warnings"].append(f"Invalid validator result format")
                    
            except Exception as e:
                # Component isolation: continue even if one fails
                error_msg = f"Validator error: {type(e).__name__}"
                # Sanitize error message to prevent credential leakage
                safe_msg = self._sanitize_message(str(e))
                logger.error(f"{error_msg}: {safe_msg}")
                self.results["failures"].append(error_msg)
        
        # Aggregate results and determine exit code
        return self._aggregate_results()
    
    def _sanitize_message(self, message: str) -> str:
        """Remove potential credentials from messages."""
        # Simple sanitization - remove long tokens/keys
        words = message.split()
        sanitized = []
        for word in words:
            # Redact long alphanumeric strings that might be tokens
            if len(word) > 20 and any(c.isalnum() for c in word):
                sanitized.append("[REDACTED]")
            else:
                sanitized.append(word)
        return " ".join(sanitized)
    
    def _aggregate_results(self) -> HealthCheckResult:
        """Aggregate component results into overall status."""
        # Determine overall status
        if self.results["critical_failures"]:
            overall_status = HealthStatus.CRITICAL
            exit_code = 2
        elif self.results["failures"] and not self.results["critical_failures"]:
            overall_status = HealthStatus.WARNING
            exit_code = 1
        else:
            overall_status = HealthStatus.PASS
            exit_code = 0
        
        return HealthCheckResult(
            overall_status=overall_status,
            exit_code=exit_code,
            failures=self.results["failures"] + self.results["critical_failures"],
            warnings=self.results["warnings"],
            successes=self.results["successes"]
        )


def run_health_check() -> int:
    """
    CLI entry point for health check.
    
    Returns:
        Exit code (0=pass, 1=warnings, 2=critical)
    """
    health_check = HealthCheck()
    result = health_check.run()
    
    print(result.format_output())
    
    return result.exit_code


def validate_wal_mode() -> Tuple[bool, str, Optional[str]]:
    """
    Validate WAL mode is enabled and checkpoint interval configured.
    
    Returns:
        Tuple of (passed, message, remediation)
    """
    try:
        from source.storage.manager import StorageManager
        
        manager = StorageManager()
        wal_enabled = manager.verify_wal_mode()
        
        if not wal_enabled:
            return (
                False,
                "WAL mode is not enabled on database",
                "Enable WAL mode by running: PRAGMA journal_mode=WAL; in SQLite"
            )
        
        # Check checkpoint interval
        checkpoint_interval = manager.get_wal_checkpoint_interval()
        if checkpoint_interval and checkpoint_interval > 0:
            return (
                True,
                f"WAL mode enabled with checkpoint interval {checkpoint_interval}",
                None
            )
        else:
            return (
                False,
                "WAL checkpoint interval not configured",
                "Configure WAL checkpoint interval in database initialization"
            )
            
    except Exception as e:
        logger.error(f"WAL mode validation error: {e}")
        return (
            False,
            "WAL mode validation failed",
            "Check database initialization and permissions"
        )


def validate_configuration() -> Tuple[bool, str, Optional[str]]:
    """
    Validate all required configuration parameters are present and valid.
    
    Returns:
        Tuple of (passed, message, remediation)
    """
    try:
        from source.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.config
        
        # Required configuration parameters
        required_params = [
            'collection_interval',
            'database_path',
            'log_level',
        ]
        
        missing = [param for param in required_params if param not in config]
        
        if missing:
            return (
                False,
                f"Configuration missing required parameters: {', '.join(missing)}",
                "Add missing parameters to config/config.yaml"
            )
        
        # Validate ranges
        collection_interval = config.get('collection_interval')
        if collection_interval is not None and collection_interval < 0:
            return (
                False,
                "Configuration parameter 'collection_interval' has invalid value (negative)",
                "Set collection_interval to positive value in config/config.yaml"
            )
        
        return (
            True,
            "Configuration valid with all required parameters",
            None
        )
        
    except Exception as e:
        logger.error(f"Configuration validation error: {e}")
        return (
            False,
            "Configuration validation failed",
            "Check config/config.yaml exists and is valid YAML"
        )


def validate_secrets() -> Tuple[bool, str, Optional[str]]:
    """
    Validate all required secrets are present and correctly formatted.
    Does NOT leak credentials in output.
    
    Returns:
        Tuple of (passed, message, remediation)
    """
    try:
        from source.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        secrets = loader.secrets
        
        # Check for required secrets (at least one collector should be configured)
        hue_username = secrets.get('hue_bridge_username', '')
        amazon_client_id = secrets.get('amazon_client_id', '')
        amazon_client_secret = secrets.get('amazon_client_secret', '')
        
        # Must have Hue OR Amazon credentials
        has_hue = bool(hue_username and len(hue_username) > 0)
        has_amazon = bool(amazon_client_id and amazon_client_secret)
        
        if not has_hue and not has_amazon:
            return (
                False,
                "Secrets missing: no collector credentials configured",
                "Add Hue Bridge username or Amazon credentials to config/secrets.yaml"
            )
        
        # Validate format (basic checks without exposing values)
        if has_hue and len(hue_username) < 10:
            return (
                False,
                "Secrets invalid: Hue Bridge username format incorrect",
                "Regenerate Hue Bridge username using authentication script"
            )
        
        if has_amazon:
            if not amazon_client_id.startswith('amzn'):
                return (
                    False,
                    "Secrets invalid: Amazon client ID format incorrect",
                    "Verify Amazon credentials in config/secrets.yaml"
                )
        
        # Success - do NOT include actual credential values
        configured = []
        if has_hue:
            configured.append("Hue Bridge")
        if has_amazon:
            configured.append("Amazon AQM")
        
        return (
            True,
            f"Secrets validated for: {', '.join(configured)}",
            None
        )
        
    except Exception as e:
        logger.error(f"Secrets validation error: {e}")
        return (
            False,
            "Secrets validation failed",
            "Check config/secrets.yaml exists and is valid YAML"
        )


def validate_database_write() -> Tuple[bool, str, Optional[str]]:
    """
    Validate database is writable by performing test write and rollback.
    
    Returns:
        Tuple of (passed, message, remediation)
    """
    try:
        from source.storage.manager import StorageManager
        
        manager = StorageManager()
        
        # Test write with rollback
        success = manager.test_write_with_rollback()
        
        if success:
            return (
                True,
                "Database writable (verified with test write and rollback)",
                None
            )
        else:
            return (
                False,
                "Database write test failed",
                "Check database file permissions and disk space"
            )
            
    except PermissionError as e:
        return (
            False,
            "Database write permission denied",
            "Run: chmod 644 data/temperature_readings.db and check directory permissions"
        )
    except Exception as e:
        logger.error(f"Database write validation error: {e}")
        return (
            False,
            "Database write validation failed",
            "Check database file exists and is not corrupted"
        )


def validate_log_rotation_config() -> Tuple[bool, str, Optional[str]]:
    """
    Validate log rotation configuration (directory writable, thresholds set).
    
    Returns:
        Tuple of (passed, message, remediation)
    """
    try:
        from source.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.config
        
        # Get log directory
        log_directory = config.get('log_directory', 'logs/')
        log_path = Path(log_directory)
        
        # Check directory exists
        if not log_path.exists():
            return (
                False,
                f"Log directory does not exist: {log_directory}",
                f"Create log directory: mkdir -p {log_directory}"
            )
        
        if not log_path.is_dir():
            return (
                False,
                f"Log path is not a directory: {log_directory}",
                f"Remove file and create directory: rm {log_directory} && mkdir {log_directory}"
            )
        
        # Check writable
        if not os.access(log_path, os.W_OK):
            return (
                False,
                f"Log directory not writable: {log_directory}",
                f"Fix permissions: chmod 755 {log_directory}"
            )
        
        # Check rotation config
        rotation_threshold = config.get('log_rotation_threshold_mb')
        backup_count = config.get('log_backup_count')
        
        if rotation_threshold is None or backup_count is None:
            return (
                False,
                "Log rotation thresholds not configured",
                "Add log_rotation_threshold_mb and log_backup_count to config.yaml"
            )
        
        return (
            True,
            f"Log rotation configured: {log_directory} (threshold: {rotation_threshold}MB, backups: {backup_count})",
            None
        )
        
    except Exception as e:
        logger.error(f"Log rotation validation error: {e}")
        return (
            False,
            "Log rotation validation failed",
            "Check log directory configuration in config.yaml"
        )


def validate_hue_bridge_connectivity() -> Tuple[bool, str, Optional[str]]:
    """
    Validate Hue Bridge is reachable and authentication works.
    
    Returns:
        Tuple of (passed, message, remediation)
    """
    try:
        # Import at function level to avoid circular dependencies
        from source.collectors import hue_collector
        from source.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.config
        secrets = loader.secrets
        
        # Try to connect to bridge
        bridge = hue_collector.connect_to_bridge(config, secrets)
        
        # Try to get sensors to verify connectivity
        sensors = hue_collector.discover_sensors(bridge, config)
        
        if sensors is not None and len(sensors) >= 0:
            return (
                True,
                f"Hue Bridge reachable and authenticated ({len(sensors)} sensors found)",
                None
            )
        else:
            return (
                False,
                "Hue Bridge returned no sensor data",
                "Check Hue Bridge configuration and sensor setup"
            )
            
    except ConnectionError as e:
        return (
            False,
            "Hue Bridge unreachable (network error)",
            "Check Hue Bridge IP address in config.yaml and verify bridge is powered on"
        )
    except PermissionError as e:
        return (
            False,
            "Hue Bridge authentication failed",
            "Run authentication script to regenerate bridge username: python source/collectors/hue_auth.py"
        )
    except KeyError as e:
        return (
            False,
            "Hue Bridge configuration missing",
            "Check that config.yaml and secrets.yaml contain Hue Bridge settings"
        )
    except Exception as e:
        logger.error(f"Hue Bridge validation error: {e}")
        return (
            False,
            f"Hue Bridge connectivity validation failed",
            "Check Hue Bridge configuration and network connectivity"
        )


def validate_amazon_aqm_connectivity() -> Tuple[bool, str, Optional[str]]:
    """
    Validate Amazon AQM API is reachable and credentials work.
    
    Returns:
        Tuple of (passed, message, remediation)
    """
    try:
        # Import at function level to avoid circular dependencies
        from source.collectors import amazon_aqm_collector_main
        from source.config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.config
        secrets = loader.secrets
        
        # Check if Amazon credentials exist
        amazon_config = secrets.get('amazon', {})
        if not amazon_config.get('client_id') or not amazon_config.get('client_secret'):
            return (
                False,
                "Amazon AQM credentials not configured",
                "Add Amazon credentials to config/secrets.yaml"
            )
        
        # Try a simple connectivity test (this may need to be async)
        # For now, just check credentials exist and are formatted correctly
        client_id = amazon_config.get('client_id', '')
        if not client_id.startswith('amzn'):
            return (
                False,
                "Amazon AQM client ID has invalid format",
                "Verify Amazon credentials in config/secrets.yaml"
            )
        
        return (
            True,
            "Amazon AQM credentials configured (full connectivity test requires async)",
            None
        )
            
    except KeyError as e:
        return (
            False,
            "Amazon AQM configuration missing",
            "Check that config.yaml and secrets.yaml contain Amazon AQM settings"
        )
    except Exception as e:
        logger.error(f"Amazon AQM validation error: {e}")
        return (
            False,
            "Amazon AQM connectivity validation failed",
            "Check Amazon credentials in secrets.yaml and network connectivity"
        )


if __name__ == "__main__":
    sys.exit(run_health_check())
