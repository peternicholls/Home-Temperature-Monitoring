"""
Performance measurement utilities for collection cycles and network payloads.

Sprint: 005-system-reliability
Task: T021 - Performance measurement implementation
"""

import time
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

# Thread-local storage for concurrent measurement isolation
_local = threading.local()


class PerformanceMeasurement:
    """Context manager for measuring operation duration."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return False
        
    def log_metrics(self):
        """Log performance metrics."""
        if self.duration is not None:
            logger.info(f"Performance: Operation duration: {self.duration:.3f}s")


@contextmanager
def measure_cycle_duration():
    """
    Context manager for measuring collection cycle duration.
    
    Usage:
        with measure_cycle_duration() as measurement:
            # Do work
            pass
        print(f"Duration: {measurement.duration}s")
    """
    measurement = PerformanceMeasurement()
    with measurement:
        yield measurement


def measure_network_payload(payload: Any) -> int:
    """
    Measure size of network payload in bytes.
    
    Args:
        payload: Data structure to measure (will be JSON serialized)
        
    Returns:
        Size in bytes
    """
    try:
        json_str = json.dumps(payload)
        size = len(json_str)
        return size
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to measure payload size: {e}")
        return 0


def capture_baseline(baseline_data: Dict[str, Any], filepath: str = "data/performance_baseline.json"):
    """
    Capture baseline performance metrics to file.
    
    Args:
        baseline_data: Dictionary containing baseline metrics
        filepath: Path to baseline file
    """
    baseline_file = Path(filepath)
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Add timestamp
    baseline_data["timestamp"] = datetime.now().isoformat()
    
    with open(baseline_file, 'w') as f:
        json.dump(baseline_data, f, indent=2)
    
    logger.info(f"Baseline metrics captured: {baseline_data}")


def compare_to_baseline(current_data: Dict[str, Any], filepath: str = "data/performance_baseline.json") -> Dict[str, float]:
    """
    Compare current performance to baseline.
    
    Args:
        current_data: Current performance metrics
        filepath: Path to baseline file
        
    Returns:
        Dictionary with improvement percentages
    """
    baseline_file = Path(filepath)
    
    if not baseline_file.exists():
        logger.warning(f"Baseline file not found: {filepath}")
        return {}
    
    with open(baseline_file, 'r') as f:
        baseline_data = json.load(f)
    
    comparison = {}
    
    # Calculate cycle duration improvement
    if "cycle_duration" in baseline_data and "cycle_duration" in current_data:
        baseline_duration = baseline_data["cycle_duration"]
        current_duration = current_data["cycle_duration"]
        improvement = ((baseline_duration - current_duration) / baseline_duration) * 100
        comparison["cycle_duration_improvement"] = round(improvement, 1)
    
    # Calculate payload size reduction
    if "payload_size" in baseline_data and "payload_size" in current_data:
        baseline_size = baseline_data["payload_size"]
        current_size = current_data["payload_size"]
        reduction = ((baseline_size - current_size) / baseline_size) * 100
        comparison["payload_size_reduction"] = round(reduction, 1)
    
    logger.info(f"Performance comparison: {comparison}")
    return comparison
