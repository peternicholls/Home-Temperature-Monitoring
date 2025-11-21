#!/usr/bin/env bash

# Initialize AI agent session with all critical checks and setup
#
# This script provides a comprehensive startup routine for AI agents working
# on the Home Temperature Monitoring project. It:
#   1. Displays constitution reminders
#   2. Auto-activates Python venv
#   3. Displays current feature context
#   4. Checks prerequisites
#   5. Shows tech stack summary
#   6. Reports incomplete tasks
#
# Usage: source init-agent-session.sh
#        (Must be sourced to activate venv in current shell)

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load common functions
source "$SCRIPT_DIR/common.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 INITIALIZING AI AGENT SESSION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Display constitution reminders
"$SCRIPT_DIR/show-constitution-reminders.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 ENVIRONMENT SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 2: Auto-activate venv (sourced, so it affects current shell)
echo "→ Activating Python virtual environment..."
source "$SCRIPT_DIR/auto-activate-venv.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📂 CURRENT FEATURE CONTEXT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 3: Display current feature context
eval $(get_feature_paths)

echo "Repository Root: $REPO_ROOT"
echo "Current Branch:  $CURRENT_BRANCH"
echo "Feature Dir:     $FEATURE_DIR"
echo ""

if [[ -f "$FEATURE_SPEC" ]]; then
    echo "✅ spec.md found"
else
    echo "⚠️  spec.md not found"
fi

if [[ -f "$IMPL_PLAN" ]]; then
    echo "✅ plan.md found"
else
    echo "⚠️  plan.md not found"
fi

if [[ -f "$TASKS" ]]; then
    echo "✅ tasks.md found"
else
    echo "⚠️  tasks.md not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✔️  PREREQUISITES CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 4: Check prerequisites (capture output, suppress on success)
if ! "$SCRIPT_DIR/check-prerequisites.sh" 2>&1 | grep -q "ERROR"; then
    echo "✅ Prerequisites verified"
else
    echo "⚠️  Prerequisites check found issues (see above)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛠️  TECH STACK SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 5: Display tech stack summary (condensed)
cat << 'EOF'
Default Language: Python 3.14.0+ (data collection, API integrations)
Alternatives:     Swift 6.0+ (performance-critical paths)
                  C/C++ (low-level optimization)
                  Node.js 22.14.0+ (web interfaces)

💡 Recommendation: Use Python for data collection tasks
   Profile before switching to Swift/C++

Full details: docs/tech-stack.md
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 TASK STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 6: Check for incomplete tasks
if [[ -f "$TASKS" ]]; then
    INCOMPLETE=$(grep -c '^\- \[ \]' "$TASKS" 2>/dev/null || echo "0")
    COMPLETE=$(grep -c '^\- \[X\]' "$TASKS" 2>/dev/null || echo "0")
    TOTAL=$((INCOMPLETE + COMPLETE))
    
    if [[ $TOTAL -gt 0 ]]; then
        echo "Tasks: $COMPLETE completed, $INCOMPLETE remaining (total: $TOTAL)"
        
        if [[ $INCOMPLETE -gt 0 ]]; then
            echo ""
            echo "Next incomplete tasks:"
            grep '^\- \[ \]' "$TASKS" | head -n 3 | sed 's/^/  /'
            if [[ $INCOMPLETE -gt 3 ]]; then
                echo "  ... and $((INCOMPLETE - 3)) more"
            fi
        fi
    else
        echo "No tasks found in tasks.md"
    fi
else
    echo "No tasks.md file in current feature"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ AGENT SESSION INITIALIZED - Ready to work!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

return 0 2>/dev/null || exit 0
