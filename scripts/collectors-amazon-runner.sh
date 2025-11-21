#!/bin/bash
# scripts/collectors-amazon-runner.sh
# Single collection cycle for Amazon AQM collector
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

# Helper function to get ISO 8601 timestamp with milliseconds
get_timestamp() {
    date -u +'%Y-%m-%dT%H:%M:%S.000Z'
}

# Ensure venv exists
if [ ! -d "$VENV" ]; then
    echo "{\"timestamp\":\"$(get_timestamp)\",\"level\":\"ERROR\",\"component\":\"amazon_runner\",\"message\":\"Virtual environment not found\"}" >> "$LOG_FILE"
    exit 1
fi

# Activate venv and run collection
cd "$PROJECT_ROOT"
source "$VENV/bin/activate"

# Add cycle start marker to log
echo "{\"timestamp\":\"$(get_timestamp)\",\"level\":\"INFO\",\"component\":\"amazon_runner\",\"message\":\"Starting Amazon AQM collection cycle via launchd\"}" >> "$LOG_FILE"

# Run the collector with error handling, capturing all JSON output to log
# The collector will output JSON via StructuredLogger (filter only JSON lines)
if python -m source.collectors.amazon_aqm_collector_main --collect-once 2>&1 | grep '^{' >> "$LOG_FILE"; then
    echo "{\"timestamp\":\"$(get_timestamp)\",\"level\":\"SUCCESS\",\"component\":\"amazon_runner\",\"message\":\"Amazon AQM collection cycle completed successfully\"}" >> "$LOG_FILE"
    exit 0
else
    echo "{\"timestamp\":\"$(get_timestamp)\",\"level\":\"ERROR\",\"component\":\"amazon_runner\",\"message\":\"Amazon AQM collection cycle failed\"}" >> "$LOG_FILE"
    exit 1
fi
