import yaml
import os
from typing import Any

CONFIG_PATH = "config/config.yaml"
SECRETS_PATH = "config/secrets.yaml"


def load_yaml(path: str) -> Any:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing file: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_config() -> Any:
    return load_yaml(CONFIG_PATH)


def load_secrets() -> Any:
    return load_yaml(SECRETS_PATH)


def validate_secrets_file(path: str = SECRETS_PATH) -> list:
    import yaml
    errors = []
    try:
        with open(path) as f:
            secrets = yaml.safe_load(f)
        # Example: check for required keys
        for section in ["hue", "nest", "weather"]:
            if section not in secrets:
                errors.append(f"Missing secrets section: {section}")
    except Exception as e:
        errors.append(str(e))
    return errors
