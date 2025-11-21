#!/usr/bin/env bash

# Display critical constitution reminders for AI agents
#
# This script addresses the need to remind agents of critical protocols
# from the constitution before beginning work.
#
# Usage: ./show-constitution-reminders.sh [--quiet]
#        --quiet: Suppress banner, just show reminders

QUIET=false
if [[ "${1:-}" == "--quiet" ]]; then
    QUIET=true
fi

if ! $QUIET; then
    cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  HOME TEMPERATURE MONITORING - CRITICAL REMINDERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

READ THIS FIRST before any work in this repository:

EOF
fi

cat << 'EOF'
1. ✅ ALWAYS ACTIVATE PYTHON VENV FIRST
   → source venv/bin/activate
   → Verify: which python should show HomeTemperatureMonitoring/venv/bin/python
   → Running without venv wastes time with dependency errors and test failures

2. 📚 VERIFY TECH STACK OPTIONS
   → Review: docs/tech-stack.md before choosing implementation language
   → Available: Python (default), Swift, C/C++, Node.js
   → Python 3.14.0+ for data collection and API integrations
   → Consider: Swift/C++ for performance-critical paths (profile first)

3. 🧪 TEST-DRIVEN DEVELOPMENT
   → Write tests BEFORE implementation (not 'quick and dirty' anymore)
   → Minimum 80% coverage for new code
   → Run tests as you add/edit code to keep kernel state current
   → Framework: pytest with async support and mocking

4. 🔬 RESEARCH COMPLEX FEATURES
   → Document research in research.md BEFORE coding
   → Required for: OAuth flows, GraphQL APIs, new integrations
   → Include: API investigation, experiments, failed attempts, successful patterns
   → Capture: Any other detailed work and decision rationale

5. 📝 WRITE IMPLEMENTATION REPORTS
   → After completing ANY phase, create report in docs/reports/
   → Follow: .specify/templates/commands/report-writing-process.md (20-step process)
   → Extract lessons learned to .specify/memory/lessons-learned.md
   → Review existing lessons before starting new work

6. 📖 CHECK CONSTITUTION & PROJECT OUTLINER
   → Consult .specify/memory/constitution.md before starting work
   → Review docs/project-outliner.md for project context
   → Verify compliance with principles and constraints
   → Follow sprint structure and Definition of Done

EOF

if ! $QUIET; then
    cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For full details: .specify/memory/constitution.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
fi
