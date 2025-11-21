"""
Structured JSON Logging Utility

Provides consistent JSON logging across all collectors and processes.
Each log entry is valid JSON with: timestamp, level, component, message, and optional metadata.

Usage:
    logger = StructuredLogger("hue_collector")
    logger.info("Collection started", cycle_id="hue-20251121-061500")
    logger.error("Bridge unreachable", error_code="connection_timeout", duration_ms=5000)
"""

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredLogger:
    """Emit structured JSON logs for parsing and analysis."""

    def __init__(self, component: str):
        """
        Initialize logger.

        Args:
            component: Component name (hue_collector, amazon_collector, runner_script, etc)
        """
        self.component = component

    def _format_timestamp(self) -> str:
        """Get ISO 8601 timestamp in UTC."""
        return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    def _emit(self, level: str, message: str, **metadata) -> None:
        """Emit structured log entry as JSON."""
        entry = {
            "timestamp": self._format_timestamp(),
            "level": level,
            "component": self.component,
            "message": message,
        }
        # Add any additional metadata fields
        entry.update(metadata)

        # Output as single-line JSON for log parsing
        json.dump(entry, sys.stdout, separators=(',', ':'))
        print()  # Newline after each entry
        sys.stdout.flush()  # Ensure immediate output

    def debug(self, message: str, **metadata) -> None:
        """Log DEBUG level message."""
        self._emit("DEBUG", message, **metadata)

    def info(self, message: str, **metadata) -> None:
        """Log INFO level message."""
        self._emit("INFO", message, **metadata)

    def warning(self, message: str, **metadata) -> None:
        """Log WARNING level message."""
        self._emit("WARNING", message, **metadata)

    def error(self, message: str, **metadata) -> None:
        """Log ERROR level message."""
        self._emit("ERROR", message, **metadata)

    def success(self, message: str, **metadata) -> None:
        """Log SUCCESS level message."""
        self._emit("SUCCESS", message, **metadata)


# Example usage for testing
if __name__ == "__main__":
    logger = StructuredLogger("test_component")

    # Test all log levels
    logger.debug("Debug message", extra_field="debug_value")
    logger.info("Information message", duration_ms=100, count=5)
    logger.warning("Warning message", attempt=1, max_retries=3)
    logger.error("Error message", error_code="test_error", details="Test error details")
    logger.success("Success message", items_processed=42)

    # Test with realistic collector data
    logger = StructuredLogger("hue_collector")
    logger.info(
        "Connected to Hue Bridge",
        bridge_ip="192.168.1.105",
        duration_ms=1234
    )
    logger.info(
        "Discovered temperature sensors",
        sensor_count=26,
        temperature_sensors=2,
        device_ids=["Utility", "Hall"],
        duration_ms=200
    )
    logger.success(
        "Collection completed successfully",
        readings_count=2,
        devices=[
            {"name": "Utility", "temp": 21.42, "battery": 100},
            {"name": "Hall", "temp": 20.40, "battery": 100}
        ],
        duration_ms=800,
        status="success"
    )
