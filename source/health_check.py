"""
Health check framework for production deployment validation.

Sprint: 005-system-reliability
Task: T030 - Health check framework implementation
"""

import sys
import time
import logging
from enum import Enum
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
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
        lines = []
        lines.append("=" * 60)
        lines.append("HEALTH CHECK REPORT")
        lines.append("=" * 60)
        lines.append(f"Overall Status: {self.overall_status.value.upper()}")
        lines.append("")
        
        if self.successes:
            lines.append("✓ PASSED CHECKS:")
            for success in self.successes:
                lines.append(f"  ✓ {success}")
            lines.append("")
        
        if self.warnings:
            lines.append("⚠ WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")
            lines.append("")
        
        if self.failures:
            lines.append("✗ FAILURES:")
            for failure in self.failures:
                lines.append(f"  ✗ {failure}")
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


if __name__ == "__main__":
    sys.exit(run_health_check())
