#!/bin/bash
# scripts/collectors-nest-runner.sh
# Single collection cycle for Nest via Amazon collector
# Runs every 5 minutes via launchd
# Captures structured JSON logs to combined collection.log

set -e

# Get absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/collection.log"

# Create logs directory if needed
mkdir -p "$LOG_DIR"

# Ensure venv exists
if [ ! -d "$VENV" ]; then
    echo "ERROR: Virtual environment not found at $VENV" >&2
    exit 1
fi

# Activate venv and run collection
cd "$PROJECT_ROOT"
source "$VENV/bin/activate"

# Run the collector - StructuredLogger writes directly to log file with locking
if python -m source.collectors.nest_via_amazon_collector_main --collect-once > /dev/null 2>&1; then
    exit 0
else
    exit 1
fi
