from typing import Any
import re

LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
DEVICE_ID_PATTERN = re.compile(r'^[a-z_]+:[a-zA-Z0-9_-]+$')


def validate_config(config: Any) -> list:
    errors = []
    # Collection interval
    interval = config.get("collection", {}).get("interval_seconds", 300)
    if not (isinstance(interval, int) and interval >= 60):
        errors.append("collection.interval_seconds must be integer >= 60")
    # Database path
    db_path = config.get("storage", {}).get("database_path", "data/readings.db")
    if not isinstance(db_path, str) or not db_path:
        errors.append("storage.database_path must be a non-empty string")
    # Log level
    log_level = config.get("logging", {}).get("level", "INFO")
    if log_level not in LOG_LEVELS:
        errors.append(f"logging.level must be one of {LOG_LEVELS}")
    # Retry attempts
    attempts = config.get("collection", {}).get("retry_attempts", 3)
    if not (isinstance(attempts, int) and 1 <= attempts <= 10):
        errors.append("collection.retry_attempts must be integer 1-10")
    # Backoff base
    backoff = config.get("collection", {}).get("retry_backoff_base", 1.0)
    if not (isinstance(backoff, float) or isinstance(backoff, int)) or backoff <= 0:
        errors.append("collection.retry_backoff_base must be > 0")
    
    # Hue-specific validation
    hue_config = config.get("collectors", {}).get("hue", {})
    if hue_config:
        # Bridge IP validation (optional, can be null for auto-discovery)
        bridge_ip = hue_config.get("bridge_ip")
        if bridge_ip is not None and not isinstance(bridge_ip, str):
            errors.append("collectors.hue.bridge_ip must be string or null")
        
        # Auto-discover flag
        auto_discover = hue_config.get("auto_discover", True)
        if not isinstance(auto_discover, bool):
            errors.append("collectors.hue.auto_discover must be boolean")
        
        # Collection interval
        hue_interval = hue_config.get("collection_interval", 300)
        if not (isinstance(hue_interval, int) and hue_interval >= 60):
            errors.append("collectors.hue.collection_interval must be integer >= 60")
    
    return errors


def validate_secrets(secrets: Any) -> list:
    errors = []
    # Example: check for non-empty API keys if present
    hue = secrets.get("hue", {})
    if "api_key" in hue and not hue["api_key"]:
        errors.append("hue.api_key must not be empty if present")
    if "bridge_id" in hue and not hue["bridge_id"]:
        errors.append("hue.bridge_id must not be empty if present")
    
    nest = secrets.get("nest", {})
    if "client_id" in nest and not nest["client_id"]:
        errors.append("nest.client_id must not be empty if present")
    weather = secrets.get("weather", {})
    if "api_key" in weather and not weather["api_key"]:
        errors.append("weather.api_key must not be empty if present")
    return errors


def validate_schema(config: Any) -> list:
    errors = []
    # Validate required top-level keys
    for section in ["collection", "storage", "logging", "validation", "collectors"]:
        if section not in config:
            errors.append(f"Missing section: {section}")
    # Validate types and ranges for collection
    collection = config.get("collection", {})
    if not isinstance(collection.get("interval_seconds", None), int):
        errors.append("collection.interval_seconds must be integer")
    # Add more schema checks as needed
    return errors
