#!/bin/bash
# scripts/collectors-hue-runner.sh
# Single collection cycle for Hue collector
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
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Hue collection cycle..."

# Run the collector with error handling
if python -m source.collectors.hue_collector --collect-once 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hue collection completed successfully"
    exit 0
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Hue collection failed" >&2
    exit 1
fi
