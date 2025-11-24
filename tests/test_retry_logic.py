"""
Test suite for retry logic decorator with exponential backoff.

Following TDD: These tests are written BEFORE implementation and MUST FAIL initially.
Sprint: 005-system-reliability
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from source.utils.retry import retry_with_backoff, TransientError, PermanentError


class TestRetryLogic:
    """Test retry decorator with various failure scenarios."""

    def test_retry_success_first_attempt(self):
        """Test successful operation on first attempt (no retry needed)."""
        mock_func = Mock(return_value="success")
        decorated = retry_with_backoff(max_attempts=3)(mock_func)
        
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_success_after_transient_failure(self):
        """Test retry succeeds after transient failure."""
        mock_func = Mock(side_effect=[
            TransientError("Network timeout"),
            "success"
        ])
        decorated = retry_with_backoff(max_attempts=3)(mock_func)
        
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 2

    def test_retry_exponential_backoff_timing(self):
        """Test exponential backoff timing is correct."""
        mock_func = Mock(side_effect=[
            TransientError("Timeout"),
            TransientError("Timeout"),
            "success"
        ])
        
        base_delay = 0.1
        backoff_multiplier = 2
        decorated = retry_with_backoff(
            max_attempts=3,
            base_delay=base_delay,
            backoff_multiplier=backoff_multiplier
        )(mock_func)
        
        start = time.time()
        result = decorated()
        elapsed = time.time() - start
        
        # Expected delays: 0.1s + 0.2s = 0.3s minimum
        assert result == "success"
        assert elapsed >= 0.3
        assert mock_func.call_count == 3

    def test_retry_exhaustion_after_max_attempts(self):
        """Test retry exhaustion raises exception after max attempts."""
        mock_func = Mock(side_effect=TransientError("Always fails"))
        decorated = retry_with_backoff(max_attempts=3, base_delay=0.01)(mock_func)
        
        with pytest.raises(TransientError, match="Always fails"):
            decorated()
        
        assert mock_func.call_count == 3

    def test_retry_permanent_error_no_retry(self):
        """Test permanent errors are not retried."""
        mock_func = Mock(side_effect=PermanentError("Invalid credentials"))
        decorated = retry_with_backoff(max_attempts=3)(mock_func)
        
        with pytest.raises(PermanentError, match="Invalid credentials"):
            decorated()
        
        # Should fail immediately without retries
        assert mock_func.call_count == 1

    def test_retry_rate_limit_backoff(self):
        """Test rate limit errors trigger appropriate backoff."""
        mock_func = Mock(side_effect=[
            TransientError("Rate limit exceeded"),
            TransientError("Rate limit exceeded"),
            "success"
        ])
        
        base_delay = 0.1
        decorated = retry_with_backoff(
            max_attempts=3,
            base_delay=base_delay,
            backoff_multiplier=2
        )(mock_func)
        
        start = time.time()
        result = decorated()
        elapsed = time.time() - start
        
        assert result == "success"
        # Verify backoff occurred (0.1s + 0.2s minimum)
        assert elapsed >= 0.3

    @patch('source.utils.retry.logger')
    def test_retry_logging_events(self, mock_logger):
        """Test comprehensive logging of retry events."""
        mock_func = Mock(side_effect=[
            TransientError("Network error"),
            "success"
        ])
        mock_func.__name__ = "test_operation"
        
        decorated = retry_with_backoff(max_attempts=3, base_delay=0.01)(mock_func)
        result = decorated()
        
        assert result == "success"
        
        # Verify retry event was logged
        assert mock_logger.warning.called
        log_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("Network error" in str(call) for call in log_calls)

    def test_retry_concurrent_operations(self):
        """Test retry logic is thread-safe for concurrent operations."""
        call_counts = {"func1": 0, "func2": 0}
        
        def failing_func(name):
            call_counts[name] += 1
            if call_counts[name] < 2:
                raise TransientError(f"{name} failed")
            return f"{name} success"
        
        decorated1 = retry_with_backoff(max_attempts=3, base_delay=0.01)(
            lambda: failing_func("func1")
        )
        decorated2 = retry_with_backoff(max_attempts=3, base_delay=0.01)(
            lambda: failing_func("func2")
        )
        
        results = {}
        
        def run_func1():
            results["func1"] = decorated1()
        
        def run_func2():
            results["func2"] = decorated2()
        
        thread1 = threading.Thread(target=run_func1)
        thread2 = threading.Thread(target=run_func2)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        assert results["func1"] == "func1 success"
        assert results["func2"] == "func2 success"
        assert call_counts["func1"] == 2
        assert call_counts["func2"] == 2
