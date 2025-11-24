#!/usr/bin/env bash

# Verify Python venv is active and correct
#
# This script enforces Constitution Critical Reminder #1:
# "ALWAYS ACTIVATE PYTHON VENV FIRST before any Python commands"
#
# Usage: source verify-venv.sh (from other scripts)
#        ./verify-venv.sh (standalone check)
#
# Exit codes:
#   0 - venv is active and correct
#   1 - venv not active or wrong venv
#   2 - venv directory doesn't exist

# Get repository root
if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
else
    # Fallback for non-git repos
    SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
fi

EXPECTED_VENV="$REPO_ROOT/venv"

# Check if venv directory exists
if [[ ! -d "$EXPECTED_VENV" ]]; then
    echo "❌ ERROR: Python venv directory not found: $EXPECTED_VENV" >&2
    echo "   Create venv: python3 -m venv venv" >&2
    exit 2
fi

# Check if venv is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ ERROR: Python virtual environment not activated" >&2
    echo "" >&2
    echo "   Constitution Critical Reminder #1:" >&2
    echo "   ALWAYS ACTIVATE PYTHON VENV FIRST before any Python commands" >&2
    echo "" >&2
    echo "   Activate now:" >&2
    echo "   → source venv/bin/activate" >&2
    echo "" >&2
    echo "   Or use:" >&2
    echo "   → source .specify/scripts/bash/auto-activate-venv.sh" >&2
    exit 1
fi

# Verify it's the correct venv
if [[ "$VIRTUAL_ENV" != "$EXPECTED_VENV" ]]; then
    echo "❌ ERROR: Wrong venv activated" >&2
    echo "" >&2
    echo "   Expected: $EXPECTED_VENV" >&2
    echo "   Actual:   $VIRTUAL_ENV" >&2
    echo "" >&2
    echo "   Deactivate current venv, then activate correct one:" >&2
    echo "   → deactivate" >&2
    echo "   → source venv/bin/activate" >&2
    exit 1
fi

# Success - venv is active and correct
echo "✅ Python venv verified: $VIRTUAL_ENV"

# Optionally show Python path if verbose
if [[ "${1:-}" == "-v" || "${1:-}" == "--verbose" ]]; then
    echo "   Python executable: $(which python)"
    echo "   Python version: $(python --version 2>&1)"
fi

exit 0
