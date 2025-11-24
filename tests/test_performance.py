"""
Test suite for performance measurement utilities.

Following TDD: These tests are written BEFORE implementation and MUST FAIL initially.
Sprint: 005-system-reliability
"""

import pytest
import time
import json
import threading
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from source.utils.performance import (
    PerformanceMeasurement,
    measure_cycle_duration,
    measure_network_payload,
    capture_baseline,
    compare_to_baseline
)


class TestPerformanceMeasurement:
    """Test performance measurement utilities."""

    def test_measure_collection_cycle_duration(self):
        """Test measurement of collection cycle duration."""
        with measure_cycle_duration() as measurement:
            time.sleep(0.1)
        
        duration = measurement.duration
        assert duration >= 0.1
        assert duration < 0.2  # Should complete quickly
        assert isinstance(duration, float)

    def test_measure_network_payload_size(self):
        """Test measurement of network payload size."""
        test_payload = {"sensors": [{"id": 1, "temp": 20.5}] * 100}
        
        size = measure_network_payload(test_payload)
        
        assert isinstance(size, int)
        assert size > 0
        # JSON serialization should produce reasonable size
        assert size == len(json.dumps(test_payload))

    def test_baseline_capture_and_comparison(self):
        """Test baseline capture and comparison functionality."""
        baseline_data = {
            "cycle_duration": 2.5,
            "payload_size": 5000,
            "timestamp": "2025-11-20T10:00:00"
        }
        
        baseline_file = Path("data/performance_baseline.json")
        
        # Capture baseline
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("pathlib.Path.parent", new_callable=lambda: MagicMock()):
                capture_baseline(baseline_data)
        
        # Compare to baseline
        current_data = {
            "cycle_duration": 1.75,  # 30% faster
            "payload_size": 2500     # 50% smaller
        }
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(baseline_data))):
                comparison = compare_to_baseline(current_data)
        
        assert "cycle_duration_improvement" in comparison
        assert "payload_size_reduction" in comparison
        assert comparison["cycle_duration_improvement"] == 30.0
        assert comparison["payload_size_reduction"] == 50.0

    @patch('source.utils.performance.logger')
    def test_performance_metrics_logging(self, mock_logger):
        """Test performance metrics are logged correctly."""
        with measure_cycle_duration() as measurement:
            time.sleep(0.05)
        
        measurement.log_metrics()
        
        assert mock_logger.info.called
        log_message = str(mock_logger.info.call_args)
        assert "duration" in log_message.lower() or "performance" in log_message.lower()

    def test_concurrent_measurement_isolation(self):
        """Test concurrent measurements don't interfere with each other."""
        results = {}
        
        def measure_operation(name, sleep_time):
            with measure_cycle_duration() as measurement:
                time.sleep(sleep_time)
            results[name] = measurement.duration
        
        thread1 = threading.Thread(target=measure_operation, args=("op1", 0.1))
        thread2 = threading.Thread(target=measure_operation, args=("op2", 0.2))
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Each measurement should reflect its own duration
        assert 0.1 <= results["op1"] < 0.15
        assert 0.2 <= results["op2"] < 0.25
