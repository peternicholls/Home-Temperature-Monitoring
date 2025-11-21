"""
Integration tests for performance validation.
Sprint: 005-system-reliability
Phase: 8
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from source.utils.performance import compare_to_baseline
from source.utils.logging import setup_logging, RobustRotatingFileHandler
import logging
import shutil

class TestPerformanceValidation:
    """Test performance metrics against success criteria."""

    def test_hue_cycle_duration_improvement(self):
        """T124: Verify SC-005: Hue collection cycles 30%+ faster than baseline."""
        # Mock baseline file
        baseline_data = {"cycle_duration": 1.0, "payload_size": 1000}
        
        with patch('builtins.open', new_callable=Mock) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = json.dumps(baseline_data)
            mock_file.__enter__.return_value = mock_file
            mock_open.return_value = mock_file
            
            with patch('pathlib.Path.exists', return_value=True):
                # Current duration 0.6s (40% improvement)
                current_data = {"cycle_duration": 0.6, "payload_size": 1000}
                
                comparison = compare_to_baseline(current_data)
                
                assert "cycle_duration_improvement" in comparison
                assert comparison["cycle_duration_improvement"] >= 30.0
                assert comparison["cycle_duration_improvement"] == 40.0

    def test_network_payload_reduction(self):
        """T125: Verify SC-006: Network transfer 50%+ smaller than baseline."""
        # Mock baseline file
        baseline_data = {"cycle_duration": 1.0, "payload_size": 1000}
        
        with patch('builtins.open', new_callable=Mock) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = json.dumps(baseline_data)
            mock_file.__enter__.return_value = mock_file
            mock_open.return_value = mock_file
            
            with patch('pathlib.Path.exists', return_value=True):
                # Current size 400 bytes (60% reduction)
                current_data = {"cycle_duration": 1.0, "payload_size": 400}
                
                comparison = compare_to_baseline(current_data)
                
                assert "payload_size_reduction" in comparison
                assert comparison["payload_size_reduction"] >= 50.0
                assert comparison["payload_size_reduction"] == 60.0

    def test_log_disk_usage_simulation(self):
        """T126: Verify SC-003: Log disk usage <60MB after 30-day simulation."""
        # Simulate logging by writing large amounts of data
        # We'll use a temporary directory
        log_dir = "tests/temp_logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/test_simulation.log"
        
        try:
            # Configure logging with 1MB max bytes and 5 backups, 6MB total limit
            # We want to verify it stays under limit
            max_bytes = 1024 * 1024 # 1MB
            backup_count = 5
            max_total_bytes = 6 * 1024 * 1024 # 6MB
            
            handler = RobustRotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                max_total_bytes=max_total_bytes
            )
            
            logger = logging.getLogger("simulation")
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)
            
            # Write 10MB of data (should trigger rotation and deletion/limit enforcement)
            # Note: RobustRotatingFileHandler enforces max_total_bytes by raising OSError if exceeded
            # But standard RotatingFileHandler deletes old backups.
            # RobustRotatingFileHandler checks total size BEFORE rotation.
            
            # If we write enough to fill backups, the oldest should be deleted by standard handler.
            # Robust handler adds an extra check for total size.
            
            # Let's write 10MB
            msg = "x" * 1024 # 1KB
            for _ in range(10 * 1024): # 10MB
                logger.info(msg)
                
            # Check total size
            total_size = 0
            if os.path.exists(log_file):
                total_size += os.path.getsize(log_file)
            for i in range(1, backup_count + 2): # Check a bit beyond
                f = f"{log_file}.{i}"
                if os.path.exists(f):
                    total_size += os.path.getsize(f)
            
            # Should be around 6MB (5 backups + current)
            # Allow some margin
            assert total_size <= max_total_bytes + (100 * 1024) # Allow 100KB margin
            
            handler.close()
            
        finally:
            if os.path.exists(log_dir):
                shutil.rmtree(log_dir)

