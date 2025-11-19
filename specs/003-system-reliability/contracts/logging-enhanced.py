#!/usr/bin/env python3
"""
Enhanced Logging Setup with Rotation Support

Sprint 1.1 Enhancement: RotatingFileHandler for automatic log rotation
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(config: dict = None):
    """
    Setup logging with rotation support.
    
    Args:
        config: Configuration dictionary with logging settings
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
    
    # File handler with rotation (optional)
    if enable_file_logging and log_file_path:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            filename=log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers
    )
    
    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, file_logging={enable_file_logging}")
    if enable_file_logging:
        logger.info(f"Log file: {log_file_path} (max_bytes={max_bytes}, backup_count={backup_count})")


# Usage example:
if __name__ == '__main__':
    config = {
        'logging': {
            'level': 'INFO',
            'enable_file_logging': True,
            'log_file_path': 'logs/hue_collection.log',
            'max_bytes': 10485760,  # 10MB
            'backup_count': 5,
            'encoding': 'utf-8',
        }
    }
    
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info("This is a test log entry")
    logger.warning("This is a warning")
    logger.error("This is an error")
