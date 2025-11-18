import logging
import os

def setup_logging(log_level: str = "INFO", log_to_file: bool = False, log_file_path: str = None):
    level = getattr(logging, log_level.upper(), logging.INFO)
    handlers = [logging.StreamHandler()]
    if log_to_file and log_file_path:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        handlers.append(logging.FileHandler(log_file_path))
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers
    )
