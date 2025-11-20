import logging
import os

from logging.handlers import RotatingFileHandler

def setup_logging(log_level: str = "INFO", log_to_file: bool = False, 
                  log_file_path: str = None, max_bytes: int = 10*1024*1024, 
                  backup_count: int = 5):
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    handlers = [logging.StreamHandler()]
    
    if log_to_file and log_file_path:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        # Use RotatingFileHandler instead of FileHandler
        handlers.append(RotatingFileHandler(
            log_file_path, 
            maxBytes=max_bytes, 
            backupCount=backup_count
        ))
        
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers
    )
