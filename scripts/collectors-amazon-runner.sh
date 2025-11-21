#!/bin/bash
# scripts/collectors-amazon-runner.sh
# Single collection cycle for Amazon AQM collector
# Runs every 5 minutes via launchd

set -e

# Get absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$PROJECT_ROOT/venv"

# Ensure venv exists
if [ ! -d "$VENV" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Virtual environment not found at $VENV" >&2
    exit 1
fi

# Activate venv and run collection
cd "$PROJECT_ROOT"
source "$VENV/bin/activate"

# Log timestamp
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Amazon AQM collection cycle..."

# Run the collector with error handling
if python -m source.collectors.amazon_aqm_collector_main 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Amazon AQM collection completed successfully"
    exit 0
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Amazon AQM collection failed" >&2
    exit 1
fi
