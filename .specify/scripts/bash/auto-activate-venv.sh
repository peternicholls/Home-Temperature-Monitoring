#!/usr/bin/env bash

# Auto-activate Python venv if in HomeTemperatureMonitoring directory
# 
# This script addresses Constitution Critical Reminder #1:
# "ALWAYS ACTIVATE PYTHON VENV FIRST before any Python commands"
#
# Usage: source auto-activate-venv.sh
#        (or call from init-agent-session.sh)

# Get repository root
if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
else
    # Fallback for non-git repos
    SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
fi

VENV_PATH="$REPO_ROOT/venv/bin/activate"

# Check if venv exists
if [[ ! -f "$VENV_PATH" ]]; then
    echo "⚠️  Warning: Python venv not found at $VENV_PATH" >&2
    echo "   Create venv: python3 -m venv venv" >&2
    return 1 2>/dev/null || exit 1
fi

# Check if already activated
if [[ -n "$VIRTUAL_ENV" ]]; then
    # Verify it's the correct venv
    EXPECTED_VENV="$REPO_ROOT/venv"
    if [[ "$VIRTUAL_ENV" == "$EXPECTED_VENV" ]]; then
        echo "✅ Python venv already active: $VIRTUAL_ENV"
        return 0 2>/dev/null || exit 0
    else
        echo "⚠️  Warning: Different venv is active" >&2
        echo "   Expected: $EXPECTED_VENV" >&2
        echo "   Actual: $VIRTUAL_ENV" >&2
        echo "   Deactivate first, then source this script again" >&2
        return 1 2>/dev/null || exit 1
    fi
fi

# Activate venv
source "$VENV_PATH"

if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "✅ Python venv activated: $VIRTUAL_ENV"
    echo "   Python: $(which python)"
    return 0 2>/dev/null || exit 0
else
    echo "❌ ERROR: Failed to activate venv" >&2
    return 1 2>/dev/null || exit 1
fi
