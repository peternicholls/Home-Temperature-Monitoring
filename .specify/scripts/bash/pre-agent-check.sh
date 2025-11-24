#!/usr/bin/env bash
# Pre-agent execution checks - runs BEFORE any SpecKit agent outline
# 
# Exit codes:
#   0 - All checks passed, proceed
#   1 - Critical failure, BLOCK execution
#   2 - Warning only, proceed but notify user

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

#============================================================================
# 1. Display Constitution Reminders
#============================================================================

if [[ -f "$REPO_ROOT/.specify/memory/constitution.md" ]]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 CONSTITUTION REMINDERS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Show critical reminders if show-constitution-reminders.sh exists
    if [[ -f "$SCRIPT_DIR/show-constitution-reminders.sh" ]]; then
        bash "$SCRIPT_DIR/show-constitution-reminders.sh" --quiet || true
    else
        # Fallback: Show first 10 lines of constitution
        head -n 10 "$REPO_ROOT/.specify/memory/constitution.md"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

#============================================================================
# 2. Python Projects: Virtual Environment Check
#============================================================================

if [[ -d "$REPO_ROOT/source" ]] && find "$REPO_ROOT/source" -name '*.py' -print -quit 2>/dev/null | grep -q .; then
    echo "🐍 Python project detected - checking virtual environment..."
    
    if [[ -z "$VIRTUAL_ENV" ]]; then
        # Try to auto-activate using existing helper script
        if [[ -f "$SCRIPT_DIR/auto-activate-venv.sh" ]]; then
            echo "   Activating virtual environment..."
            if source "$SCRIPT_DIR/auto-activate-venv.sh" 2>/dev/null; then
                echo "   ✅ Virtual environment activated"
            else
                echo "❌ ERROR: Could not activate Python venv" >&2
                echo "   Run: python3 -m venv venv && source venv/bin/activate" >&2
                exit 1  # BLOCK execution
            fi
        else
            # Fallback: Try direct activation
            if [[ -f "$REPO_ROOT/venv/bin/activate" ]]; then
                echo "   Activating virtual environment..."
                source "$REPO_ROOT/venv/bin/activate"
                echo "   ✅ Virtual environment activated"
            else
                echo "❌ ERROR: Python virtual environment required but not active" >&2
                echo "   Run: python3 -m venv venv && source venv/bin/activate" >&2
                exit 1  # BLOCK execution
            fi
        fi
    else
        echo "   ✅ Virtual environment active: $VIRTUAL_ENV"
    fi
    echo ""
fi

#============================================================================
# 3. Node.js Projects: Dependencies Check
#============================================================================

if [[ -f "$REPO_ROOT/package.json" ]]; then
    echo "📦 Node.js project detected - checking dependencies..."
    
    if [[ ! -d "$REPO_ROOT/node_modules" ]]; then
        echo "⚠️  WARNING: node_modules/ not found" >&2
        echo "   Run: npm install" >&2
        exit 2  # Warning only, don't block
    else
        echo "   ✅ Dependencies installed"
    fi
    echo ""
fi

#============================================================================
# 4. Rust Projects: Cargo Check
#============================================================================

if [[ -f "$REPO_ROOT/Cargo.toml" ]]; then
    echo "🦀 Rust project detected - checking cargo..."
    
    if ! command -v cargo &> /dev/null; then
        echo "❌ ERROR: cargo command not found" >&2
        echo "   Install Rust: https://rustup.rs/" >&2
        exit 1  # BLOCK execution
    else
        echo "   ✅ Cargo available: $(cargo --version)"
    fi
    echo ""
fi

#============================================================================
# 5. Custom Project Checks (Add Your Own Below)
#============================================================================

# Example: Check database connection
# if ! nc -z localhost 5432 >/dev/null 2>&1; then
#     echo "⚠️  WARNING: PostgreSQL not running on localhost:5432" >&2
#     exit 2  # Warning only
# fi

# Example: Check Docker daemon
# if ! docker info >/dev/null 2>&1; then
#     echo "⚠️  WARNING: Docker daemon not running" >&2
#     exit 2  # Warning only
# fi

#============================================================================
# Success
#============================================================================

exit 0
