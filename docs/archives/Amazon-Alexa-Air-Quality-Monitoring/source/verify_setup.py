# Quick verification script for Sprint 0 setup
import os
import sys
import yaml

CONFIG_PATH = "config/config.yaml"
SECRETS_PATH = "config/secrets.yaml"
DB_PATH = "data/readings.db"

errors = []

# Check Python version
if sys.version_info < (3, 11):
    errors.append(f"Python version is {sys.version_info.major}.{sys.version_info.minor}, must be >= 3.11")

# Check config file
if not os.path.isfile(CONFIG_PATH):
    errors.append(f"Missing config file: {CONFIG_PATH}")
else:
    try:
        with open(CONFIG_PATH) as f:
            yaml.safe_load(f)
    except Exception as e:
        errors.append(f"Config YAML error: {e}")

# Check secrets file
if not os.path.isfile(SECRETS_PATH):
    errors.append(f"Missing secrets file: {SECRETS_PATH}")
else:
    try:
        with open(SECRETS_PATH) as f:
            yaml.safe_load(f)
    except Exception as e:
        errors.append(f"Secrets YAML error: {e}")

# Check database file
if not os.path.isfile(DB_PATH):
    errors.append(f"Missing database file: {DB_PATH}")

if errors:
    print("Setup verification failed:")
    for err in errors:
        print(f"- {err}")
    sys.exit(1)
else:
    print("Setup verification passed. All files present and valid.")
