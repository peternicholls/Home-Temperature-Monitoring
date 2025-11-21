#!/usr/bin/env python3
"""
Enhanced Logging Setup with Production-Ready Rotation Support

Sprint 005: Production hardening with retry logic, disk usage validation,
and graceful error handling

Features:
- Retry logic for file system errors (3 attempts, exponential backoff)
- Disk usage validation (configurable max total usage)
- Low disk space graceful degradation
- Rotation failure critical error logging
- Thread-safe concurrent logging during rotation
"""

import logging
import os
import time
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path


class RobustRotatingFileHandler(RotatingFileHandler):
    """
    Enhanced RotatingFileHandler with production hardening:
    - Retry logic for file system errors
    - Disk usage validation
    - Low disk space handling
    - Thread-safe rotation
    """
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0,
                 encoding=None, delay=False, errors=None, 
                 max_total_bytes=None, retry_attempts=3, retry_base_delay=0.1):
        """
        Initialize robust rotating file handler.
        
        Args:
            filename: Log file path
            mode: File open mode
            maxBytes: Max bytes per file before rotation
            backupCount: Number of backup files to keep
            encoding: File encoding
            delay: Delay file opening
            errors: Error handling strategy
            max_total_bytes: Max total disk usage for all log files (None = no limit)
            retry_attempts: Number of retry attempts for file operations
            retry_base_delay: Base delay for exponential backoff (seconds)
        """
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay, errors)
        self.max_total_bytes = max_total_bytes
        self.retry_attempts = retry_attempts
        self.retry_base_delay = retry_base_delay
        self._rotation_lock = threading.Lock()
        
    def doRollover(self):
        """
        Perform log rotation with retry logic and error handling.
        """
        # Acquire lock for thread-safe rotation
        with self._rotation_lock:
            try:
                self._doRolloverWithRetry()
            except Exception as e:
                # Critical error: rotation failed after all retries
                self._handleRotationFailure(e)
    
    def _doRolloverWithRetry(self):
        """
        Perform rollover with retry logic for file system errors.
        """
        last_exception = None
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                # Check disk usage before rotation
                if self.max_total_bytes:
                    self._validateDiskUsage()
                
                # Perform standard rotation
                super().doRollover()
                
                # Success - log event if not first attempt
                if attempt > 1:
                    print(f"Log rotation succeeded on attempt {attempt}/{self.retry_attempts}", 
                          file=self.stream)
                
                return
                
            except OSError as e:
                last_exception = e
                
                # Check if error is transient or permanent
                if self._isPermanentError(e):
                    # Don't retry permanent errors
                    raise
                
                # Transient error - retry with exponential backoff
                if attempt < self.retry_attempts:
                    delay = self.retry_base_delay * (2 ** (attempt - 1))
                    print(f"Log rotation attempt {attempt}/{self.retry_attempts} failed: {e}. "
                          f"Retrying in {delay:.2f}s...", file=self.stream)
                    time.sleep(delay)
                else:
                    # All retries exhausted
                    raise
        
        # Should not reach here, but raise last exception if we do
        if last_exception:
            raise last_exception
    
    def _validateDiskUsage(self):
        """
        Validate total disk usage doesn't exceed configured limit.
        Raises OSError if limit exceeded.
        """
        if not self.max_total_bytes:
            return
        
        try:
            # Calculate total size of all log files
            total_size = 0
            base_filename = self.baseFilename
            
            # Main log file
            if os.path.exists(base_filename):
                total_size += os.path.getsize(base_filename)
            
            # Backup files (.1, .2, .3, etc.)
            for i in range(1, self.backupCount + 1):
                backup_file = f"{base_filename}.{i}"
                if os.path.exists(backup_file):
                    total_size += os.path.getsize(backup_file)
            
            # Check if limit exceeded
            if total_size > self.max_total_bytes:
                raise OSError(28, f"Total log disk usage {total_size} bytes exceeds limit {self.max_total_bytes} bytes")
                
        except OSError:
            raise
        except Exception as e:
            # Non-fatal error in disk usage calculation - log and continue
            print(f"Warning: Failed to validate disk usage: {e}", file=self.stream)
    
    def _isPermanentError(self, error):
        """
        Determine if an OSError is permanent (don't retry) or transient (retry).
        
        Permanent errors:
        - ENOENT (2): No such file or directory (bad configuration)
        - EACCES (13): Permission denied (security issue)
        - ENOSPC (28): No space left on device (disk full)
        - EROFS (30): Read-only file system
        
        Transient errors:
        - EAGAIN (11): Resource temporarily unavailable
        - EBUSY (16): Device or resource busy
        - ETXTBSY (26): Text file busy
        """
        permanent_errnos = {2, 13, 28, 30}  # ENOENT, EACCES, ENOSPC, EROFS
        return error.errno in permanent_errnos
    
    def _handleRotationFailure(self, error):
        """
        Handle rotation failure after all retries exhausted.
        Log critical error and continue with console logging.
        """
        try:
            # Create critical error message
            error_msg = (
                f"CRITICAL: Log rotation failed after {self.retry_attempts} attempts. "
                f"Error: {error}. File logging may be degraded. "
                f"Check disk space and file permissions for: {self.baseFilename}"
            )
            
            # Try to log to current stream (may be console if file failed)
            print(error_msg, file=self.stream)
            
            # Try to create alert file (similar to Amazon AQM token alerts)
            try:
                alert_file = Path('data/ALERT_LOG_ROTATION_FAILED.txt')
                alert_file.parent.mkdir(parents=True, exist_ok=True)
                alert_file.write_text(
                    f"Log rotation failure detected.\n"
                    f"Error: {error}\n"
                    f"Log file: {self.baseFilename}\n"
                    f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Action required: Check disk space and file permissions.\n"
                )
            except Exception as alert_error:
                print(f"Warning: Failed to create rotation alert file: {alert_error}", 
                      file=self.stream)
                
        except Exception as e:
            # Last resort - print to stderr
            import sys
            print(f"CRITICAL: Log rotation failed and error handling also failed: {e}", 
                  file=sys.stderr)


def setup_logging(config: dict = None):
    """
    Setup logging with production-ready rotation support.
    
    Args:
        config: Configuration dictionary with logging settings
    
    Configuration options:
        logging.level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logging.enable_file_logging: Enable file logging (default: True)
        logging.log_file_path: Path to log file (default: logs/hue_collection.log)
        logging.max_bytes: Max bytes per log file before rotation (default: 10MB)
        logging.backup_count: Number of backup files to keep (default: 5)
        logging.encoding: File encoding (default: utf-8)
        logging.max_total_bytes: Max total disk usage for all logs (default: 60MB)
        logging.retry_attempts: Rotation retry attempts (default: 3)
        logging.retry_base_delay: Base delay for retry backoff (default: 0.1s)
    """
    config = config or {}
    logging_config = config.get('logging', {})
    
    # Extract configuration
    log_level = logging_config.get('level', 'INFO').upper()
    enable_file_logging = logging_config.get('enable_file_logging', True)
    log_file_path = logging_config.get('log_file_path', 'logs/hue_collection.log')
    max_bytes = logging_config.get('max_bytes', 10 * 1024 * 1024)  # 10MB default
    backup_count = logging_config.get('backup_count', 5)
    encoding = logging_config.get('encoding', 'utf-8')
    max_total_bytes = logging_config.get('max_total_bytes', 60 * 1024 * 1024)  # 60MB default
    retry_attempts = logging_config.get('retry_attempts', 3)
    retry_base_delay = logging_config.get('retry_base_delay', 0.1)
    
    # Convert log level string to logging constant
    level = getattr(logging, log_level, logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup handlers
    handlers = []
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # File handler with robust rotation (optional)
    if enable_file_logging and log_file_path:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Create robust rotating file handler with production hardening
        file_handler = RobustRotatingFileHandler(
            filename=log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
            max_total_bytes=max_total_bytes,
            retry_attempts=retry_attempts,
            retry_base_delay=retry_base_delay
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, file_logging={enable_file_logging}")
    if enable_file_logging:
        logger.info(f"Log file: {log_file_path} (max_bytes={max_bytes}, backup_count={backup_count}, "
                   f"max_total_bytes={max_total_bytes}, retry_attempts={retry_attempts})")
