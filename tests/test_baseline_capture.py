"""
Tests for baseline performance capture and comparison utilities.

Sprint: 005-system-reliability
Tasks: T087-T090 - Baseline capture tests (TDD)
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from source.utils.performance import (
    measure_cycle_duration,
    measure_network_payload,
    capture_baseline,
    compare_to_baseline
)


@pytest.fixture
def temp_baseline_file(tmp_path):
    """Fixture providing temporary baseline file path."""
    return str(tmp_path / "test_baseline.json")


@pytest.fixture
def sample_baseline_data():
    """Sample baseline data for testing."""
    return {
        "cycle_duration": 5.0,
        "payload_size": 10000,
        "collector": "hue",
        "timestamp": datetime.now().isoformat()
    }


def test_capture_collection_cycle_duration():
    """
    T087: Test capturing collection cycle duration.
    
    Verifies that measure_cycle_duration context manager accurately captures
    the duration of operations.
    """
    import time
    
    # Measure a known duration
    with measure_cycle_duration() as measurement:
        time.sleep(0.1)  # 100ms
    
    # Verify duration captured
    assert measurement.duration is not None
    assert 0.09 <= measurement.duration <= 0.15  # Allow some tolerance
    assert measurement.start_time is not None
    assert measurement.end_time is not None
    assert measurement.end_time > measurement.start_time


def test_capture_network_payload_size():
    """
    T088: Test capturing network payload size.
    
    Verifies that measure_network_payload accurately calculates the size
    of JSON-serializable data structures.
    """
    # Test with various payload sizes
    small_payload = {"key": "value"}
    medium_payload = {"sensors": [{"id": i, "temp": 20.5} for i in range(10)]}
    large_payload = {"data": [{"id": i, "value": "x" * 100} for i in range(100)]}
    
    # Measure sizes
    small_size = measure_network_payload(small_payload)
    medium_size = measure_network_payload(medium_payload)
    large_size = measure_network_payload(large_payload)
    
    # Verify sizes are reasonable
    assert small_size > 0
    assert medium_size > small_size
    assert large_size > medium_size
    
    # Verify size accuracy (manual calculation)
    expected_small = len(json.dumps(small_payload))
    assert small_size == expected_small


def test_capture_network_payload_invalid_data():
    """Test that invalid payloads return 0 size."""
    # Create non-serializable object
    class NonSerializable:
        pass
    
    invalid_payload = {"obj": NonSerializable()}
    size = measure_network_payload(invalid_payload)
    
    assert size == 0


def test_baseline_storage_and_retrieval(temp_baseline_file, sample_baseline_data):
    """
    T089: Test baseline storage and retrieval.
    
    Verifies that baseline data can be stored to file and retrieved
    accurately for comparison.
    """
    # Capture baseline
    capture_baseline(sample_baseline_data, temp_baseline_file)
    
    # Verify file exists
    baseline_path = Path(temp_baseline_file)
    assert baseline_path.exists()
    
    # Retrieve and verify data
    with open(temp_baseline_file, 'r') as f:
        stored_data = json.load(f)
    
    assert stored_data["cycle_duration"] == sample_baseline_data["cycle_duration"]
    assert stored_data["payload_size"] == sample_baseline_data["payload_size"]
    assert stored_data["collector"] == sample_baseline_data["collector"]
    assert "timestamp" in stored_data


def test_baseline_storage_creates_directory(tmp_path):
    """Test that baseline capture creates parent directories if needed."""
    nested_path = str(tmp_path / "nested" / "dir" / "baseline.json")
    test_data = {"cycle_duration": 3.0, "payload_size": 5000}
    
    # Should create nested directories
    capture_baseline(test_data, nested_path)
    
    assert Path(nested_path).exists()


def test_baseline_comparison_reporting(temp_baseline_file):
    """
    T090: Test baseline comparison reporting.
    
    Verifies that compare_to_baseline accurately calculates improvement
    percentages for cycle duration and payload size.
    """
    # Create baseline
    baseline = {
        "cycle_duration": 10.0,
        "payload_size": 20000
    }
    capture_baseline(baseline, temp_baseline_file)
    
    # Test improvement scenario (30% faster, 50% smaller)
    improved_data = {
        "cycle_duration": 7.0,   # 30% improvement
        "payload_size": 10000     # 50% reduction
    }
    
    comparison = compare_to_baseline(improved_data, temp_baseline_file)
    
    # Verify improvements calculated correctly
    assert comparison["cycle_duration_improvement"] == 30.0
    assert comparison["payload_size_reduction"] == 50.0


def test_baseline_comparison_degradation(temp_baseline_file):
    """Test that comparison correctly reports performance degradation."""
    # Create baseline
    baseline = {
        "cycle_duration": 5.0,
        "payload_size": 10000
    }
    capture_baseline(baseline, temp_baseline_file)
    
    # Test degradation scenario (slower and larger)
    degraded_data = {
        "cycle_duration": 10.0,   # -100% (slower)
        "payload_size": 15000     # -50% (larger)
    }
    
    comparison = compare_to_baseline(degraded_data, temp_baseline_file)
    
    # Verify degradation reported with negative percentages
    assert comparison["cycle_duration_improvement"] == -100.0
    assert comparison["payload_size_reduction"] == -50.0


def test_baseline_comparison_missing_file(tmp_path):
    """Test that comparison handles missing baseline file gracefully."""
    non_existent_file = str(tmp_path / "missing.json")
    current_data = {
        "cycle_duration": 5.0,
        "payload_size": 10000
    }
    
    comparison = compare_to_baseline(current_data, non_existent_file)
    
    # Should return empty dict when baseline missing
    assert comparison == {}


def test_baseline_comparison_partial_data(temp_baseline_file):
    """Test comparison when only some metrics are present."""
    # Baseline with only cycle duration
    baseline = {"cycle_duration": 10.0}
    capture_baseline(baseline, temp_baseline_file)
    
    # Current data with only payload size
    current = {"payload_size": 5000}
    
    comparison = compare_to_baseline(current, temp_baseline_file)
    
    # Should not include metrics missing in either dataset
    assert "cycle_duration_improvement" not in comparison
    assert "payload_size_reduction" not in comparison


def test_baseline_multiple_captures(temp_baseline_file):
    """Test that multiple captures overwrite previous baseline."""
    # First capture
    baseline1 = {"cycle_duration": 5.0, "payload_size": 10000}
    capture_baseline(baseline1, temp_baseline_file)
    
    # Second capture (should overwrite)
    baseline2 = {"cycle_duration": 3.0, "payload_size": 8000}
    capture_baseline(baseline2, temp_baseline_file)
    
    # Verify latest data is stored
    with open(temp_baseline_file, 'r') as f:
        stored = json.load(f)
    
    assert stored["cycle_duration"] == 3.0
    assert stored["payload_size"] == 8000
