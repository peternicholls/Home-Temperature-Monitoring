# Pre-Execution Hook Exit Code Conventions

## Overview

The `.specify/scripts/bash/pre-agent-check.sh` script uses exit codes to control agent execution flow. This enables projects to enforce environment requirements and display critical reminders before any work begins.

## Exit Code Table

| Exit Code | Meaning | Agent Behavior | Use Case |
|-----------|---------|----------------|----------|
| **0** | ✅ Success | Continue to agent's Step 1 | All checks passed, ready to proceed |
| **1** | 🚨 Critical Failure | **STOP** execution | Environment broken, requires manual fix |
| **2** | ⚠️ Warning | Show warning, continue to Step 1 | Non-critical issue, can proceed with caution |

## When to Use Each Exit Code

### Exit 0 (Success)

**Use when**:
- All environment checks pass
- Required tools/dependencies present
- Configuration valid
- Ready for normal agent execution

**Example scenarios**:
- Python venv activated successfully
- Constitution reminders displayed
- All required environment variables set
- Database connection verified

### Exit 1 (Block Execution)

**Use when**:
- Critical dependency missing (e.g., no venv found)
- Invalid configuration detected
- Authentication credentials expired
- Database unreachable
- Disk space critically low
- Any condition that will cause agent to fail mid-execution

**Example scenarios**:
```bash
# venv doesn't exist and can't be created
if [[ ! -d "venv" ]]; then
    echo "🚨 CRITICAL: Python venv not found. Create with: python3 -m venv venv" >&2
    exit 1
fi

# Required environment variable missing
if [[ -z "$REQUIRED_API_KEY" ]]; then
    echo "🚨 CRITICAL: REQUIRED_API_KEY not set" >&2
    exit 1
fi

# Database connection failed
if ! sqlite3 "$DB_FILE" "SELECT 1;" &>/dev/null; then
    echo "🚨 CRITICAL: Cannot access database at $DB_FILE" >&2
    exit 1
fi
```

**Agent behavior**: Displays error message, **does NOT proceed** to Step 1

### Exit 2 (Warning)

**Use when**:
- Non-critical issue detected
- Degraded functionality but can continue
- Best practice violation (not mandatory)
- Information user should know but not blocking

**Example scenarios**:
```bash
# Optional optimization not enabled
if ! grep -q "WAL" "$DB_FILE" 2>/dev/null; then
    echo "⚠️  WARNING: Database not using WAL mode (recommended for concurrent access)" >&2
    exit 2
fi

# Low disk space (not critical yet)
if [[ $(df -h . | awk 'NR==2 {print $5}' | sed 's/%//') -gt 80 ]]; then
    echo "⚠️  WARNING: Disk usage > 80%, consider cleanup" >&2
    exit 2
fi

# Outdated dependency version
if [[ $(python --version | cut -d' ' -f2) < "3.10" ]]; then
    echo "⚠️  WARNING: Python < 3.10 detected, upgrade recommended" >&2
    exit 2
fi
```

**Agent behavior**: Displays warning message, **continues** to Step 1

## Implementation Pattern

```bash
#!/usr/bin/env bash
# .specify/scripts/bash/pre-agent-check.sh

set -euo pipefail

echo "Running pre-execution checks..."

# Success path (exit 0)
if all_checks_pass; then
    echo "✅ All checks passed"
    exit 0
fi

# Critical failure (exit 1)
if critical_issue_detected; then
    echo "🚨 CRITICAL: Cannot proceed" >&2
    exit 1
fi

# Warning path (exit 2)
if non_critical_issue_detected; then
    echo "⚠️  WARNING: Issue detected but can continue" >&2
    exit 2
fi

# Default success
exit 0
```

## Agent Integration

All SpecKit agents use this Step 0 pattern:

```markdown
0. **Pre-execution validation**: Run `.specify/scripts/bash/pre-agent-check.sh` from repo root BEFORE all other steps (if exists).
   - Check if `.specify/scripts/bash/pre-agent-check.sh` exists
   - If exists:
     - Run: `bash .specify/scripts/bash/pre-agent-check.sh`
     - Capture exit code and output
     - Exit 0: Proceed to Step 1
     - Exit 1: STOP - Display stderr, error message, do not continue
     - Exit 2: Display stdout/stderr as warning, proceed to Step 1
   - If not exists: Skip to Step 1
   - **Purpose**: Validates environment setup, activates required contexts, and displays critical constitution reminders to prevent common failure modes
```

## Testing

Test each exit code scenario:

```bash
# Test exit 0 (normal)
bash .specify/scripts/bash/pre-agent-check.sh
echo "Exit code: $?"  # Should be 0

# Test exit 1 (add temporary failure)
# Modify script: add "exit 1" before final success
# Run agent → should block execution

# Test exit 2 (add temporary warning)
# Modify script: add "exit 2" before final success  
# Run agent → should show warning but continue
```

## Best Practices

1. **Prioritize exit 0**: Most executions should be successful
2. **Reserve exit 1 for true blockers**: Only use when agent will definitely fail
3. **Use exit 2 for awareness**: Help users but don't block productivity
4. **Provide clear messages**: Explain what's wrong and how to fix
5. **Test all paths**: Verify each exit code scenario works correctly
6. **Document custom checks**: Explain why you added each validation

## Troubleshooting

**Agent ignores exit codes**:
- Verify agent file has Step 0 (check `.github/agents/speckit.*.agent.md`)
- Ensure pre-check script is executable: `chmod +x .specify/scripts/bash/pre-agent-check.sh`

**Exit 1 not blocking**:
- Check agent's Step 0 instructions match the template above
- Verify error message goes to stderr: `echo "Error" >&2`

**Exit 2 treated as failure**:
- Ensure warnings go to stdout or stderr (both work for exit 2)
- Agent should display warning but continue to Step 1

## Related Documentation

- **Pre-Check Script**: `.specify/scripts/bash/pre-agent-check.sh`
- **Template**: `.specify/templates/pre-agent-check.sh.template`
- **Testing Instructions**: `specs/006-pre-execution-hook/TESTING_INSTRUCTIONS.md`
- **Specification**: `specs/006-pre-execution-hook/spec.md`
