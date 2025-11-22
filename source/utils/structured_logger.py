"""
Structured JSON Logging Utility

Provides consistent JSON logging across all collectors and processes.
Each log entry is valid JSON with: timestamp, level, component, message, and optional metadata.

Usage:
    # Pass config dictionary with component and logging settings
    config = load_config()  # Loads from config/config.yaml
    config['component'] = 'hue_collector'  # Add component name
    logger = StructuredLogger(config)  # Only parameter is config
    logger.info("Collection started", cycle_id="hue-20251121-061500")
    logger.error("Bridge unreachable", error_code="connection_timeout", duration_ms=5000)
"""

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredLogger:
    """Emit structured JSON logs for parsing and analysis."""

    LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "SUCCESS": 50,  # Treat SUCCESS as highest level
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize logger from configuration.

        Args:
            config: Configuration dictionary (required). Must contain:
                - 'component': Component name (hue_collector, amazon_aqm_collector, etc)
                - 'logging': Optional logging config with 'level', 'enable_file_logging', 'log_file_path'
        """
        self.config = config
        self.component = config.get('component', 'unknown')
        
        # Get configured log level
        logging_config = self.config.get('logging', {})
        self.log_level_str = logging_config.get('level', 'INFO').upper()
        self.log_level = self.LEVELS.get(self.log_level_str, self.LEVELS['INFO'])
        
        # File logging setup
        self.enable_file_logging = logging_config.get('enable_file_logging', True)
        self.log_file_path = logging_config.get('log_file_path', 'logs/collection.log')

    def _should_log(self, level: str) -> bool:
        """Check if the given level should be logged based on configured level."""
        return self.LEVELS.get(level.upper(), 0) >= self.log_level

    def _format_timestamp(self) -> str:
        """Get ISO 8601 timestamp in UTC."""
        return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    def _emit(self, level: str, message: str, **metadata) -> None:
        """Emit structured log entry as JSON."""
        if not self._should_log(level):
            return
            
        entry = {
            "timestamp": self._format_timestamp(),
            "level": level,
            "component": self.component,
            "message": message,
        }
        # Add any additional metadata fields
        entry.update(metadata)

        # Output as single-line JSON for log parsing
        # Use separators to minimize size, ensure_ascii=False for unicode support
        json_line = json.dumps(entry, separators=(',', ':'), ensure_ascii=False)
        
        # Output to stdout (will be captured by runner script)
        print(json_line)
        sys.stdout.flush()  # Ensure immediate output
        
        # Also write to file if enabled
        if self.enable_file_logging:
            try:
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(json_line + '\n')
                    f.flush()
            except Exception:
                # Don't fail if file logging fails, just continue
                pass

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
    config = {
        "component": "test_component",
        "logging": {
            "level": "INFO"
        }
    }
    logger = StructuredLogger(config)

    # Test all log levels
    logger.debug("Debug message", extra_field="debug_value")
    logger.info("Information message", duration_ms=100, count=5)
    logger.warning("Warning message", attempt=1, max_retries=3)
    logger.error("Error message", error_code="test_error", details="Test error details")
    logger.success("Success message", items_processed=42)
