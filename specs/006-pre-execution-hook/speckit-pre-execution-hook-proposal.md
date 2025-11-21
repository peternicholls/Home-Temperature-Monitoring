---
description: "Proposal for generalizable pre-execution hook system in SpecKit agents"
date: "2025-11-21"
status: "DRAFT - For discussion and SpecKit contribution"
author: "Home Temperature Monitoring Project"
target: "specify/SpecKit upstream contribution"
---

# SpecKit Pre-Execution Hook Proposal

## Problem Statement

### Current Issues

1. **Project-Specific Requirements Scattered**
   - Constitution reminders buried in separate files
   - Environment validation (venv, Node, Docker) hardcoded in agent outlines
   - Each project must modify SpecKit agent files directly
   - No standardized way to inject project requirements

2. **Agents Don't Always Check Constitution**
   - Critical reminders documented but not enforced
   - Agents can start work without seeing project-specific rules
   - No automatic validation before execution begins

3. **Non-Portable Solutions**
   - Current fix: Hardcoded Python venv check in `speckit.implement.agent.md` Step 1
   - Project-specific and not generalizable to other languages/tools
   - Requires modifying SpecKit agent files per project
   - Difficult to maintain across SpecKit updates

### Real-World Example (This Project)

**Problem**: Constitution Critical Reminder #1 states "ALWAYS ACTIVATE PYTHON VENV FIRST", but agents would forget, causing:
- `ModuleNotFoundError: No module named 'phue'`
- Wasted time debugging dependency errors
- 15-20% session failure rate

**Current Hack**: Manually added to `speckit.implement.agent.md` Step 1:
```markdown
1. **Verify Python Environment** (Python projects only):
   - Check if `source/` directory exists with `.py` files
   - REQUIRED: Activate Python venv: `source .specify/scripts/bash/auto-activate-venv.sh`
   - If venv activation fails: STOP
```

**Why This Is Bad**:
- ❌ Python-specific logic in generic SpecKit agent
- ❌ Breaks for Node.js, Rust, Go, etc. projects
- ❌ Must modify SpecKit agent files (non-portable)
- ❌ Lost on SpecKit updates

---

## Proposed Solution: Pre-Execution Hook System

### Overview

Add a **standardized Step 0** to ALL SpecKit agents that runs `.specify/scripts/bash/pre-agent-check.sh` if it exists, allowing projects to inject:
- Constitution reminders
- Environment validation (venv, Node, Docker)
- Auto-fixing (activate venv, install deps)
- Project-specific requirements

### Key Design Principles

1. **Opt-In**: If `pre-agent-check.sh` doesn't exist, agents work as before (backward compatible)
2. **Language-Agnostic**: Works for Python, Node, Rust, Go, any language
3. **Configurable**: YAML config file defines what checks to run
4. **Non-Breaking**: Existing SpecKit projects unaffected
5. **Exit-Code Driven**: Script controls whether to block, warn, or proceed

---

## Implementation Plan

### 1. SpecKit Core Changes (Upstream Contribution)

**File**: ALL `speckit.*.agent.md` files (implement, plan, specify, tasks, etc.)

**Add Step 0 to Outline**:

```markdown
## Outline

0. **Pre-Execution Validation** (Project-specific requirements):
   - Check if `.specify/scripts/bash/pre-agent-check.sh` exists
   - If exists:
     - Run: `bash .specify/scripts/bash/pre-agent-check.sh`
     - Check exit code:
       - **0**: All checks passed → Proceed to step 1
       - **1**: CRITICAL FAILURE → STOP execution, display error
       - **2**: WARNING → Display warning message, proceed to step 1
   - If not exists: Skip to step 1
   - **Purpose**: Enforce project constitution, validate environment, auto-fix common issues
   - **Why This Helps**: Projects can inject custom requirements without modifying SpecKit agent files

1. Run `.specify/scripts/bash/check-prerequisites.sh --json ...
   ... (existing steps continue)
```

**Affected Files**:
- `speckit.implement.agent.md` ✅
- `speckit.plan.agent.md` ✅
- `speckit.specify.agent.md` ✅
- `speckit.tasks.agent.md` ✅
- `speckit.analyze.agent.md` ✅
- `speckit.clarify.agent.md` ✅
- `speckit.checklist.agent.md` ✅
- `speckit.constitution.agent.md` ✅

---

### 2. Reference Implementation (Template)

**File**: `.specify/templates/pre-agent-check.sh.template`

```bash
#!/usr/bin/env bash
# Pre-agent execution checks - runs BEFORE any SpecKit agent outline
# 
# Exit codes:
#   0 - All checks passed, proceed
#   1 - Critical failure, BLOCK execution
#   2 - Warning only, proceed but notify user

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load common functions if available
if [[ -f "$SCRIPT_DIR/common.sh" ]]; then
    source "$SCRIPT_DIR/common.sh"
    eval $(get_feature_paths)
fi

REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

#============================================================================
# 1. Display Constitution Reminders (if exists)
#============================================================================

CONSTITUTION_FILE="$REPO_ROOT/.specify/memory/constitution.md"
REMINDERS_SCRIPT="$SCRIPT_DIR/show-constitution-reminders.sh"

if [[ -f "$CONSTITUTION_FILE" ]] && [[ -f "$REMINDERS_SCRIPT" ]]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📖 PROJECT CONSTITUTION REMINDERS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    "$REMINDERS_SCRIPT" --quiet || true
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

#============================================================================
# 2. Language-Specific Environment Checks
#============================================================================

# Python projects: Check/activate venv
if [[ -d "$REPO_ROOT/source" ]] && find "$REPO_ROOT/source" -name '*.py' -print -quit 2>/dev/null | grep -q .; then
    if [[ -f "$SCRIPT_DIR/auto-activate-venv.sh" ]]; then
        echo "🐍 Python project detected - checking virtual environment..."
        if source "$SCRIPT_DIR/auto-activate-venv.sh" 2>/dev/null; then
            echo "✅ Python venv activated"
        else
            echo "❌ ERROR: Could not activate Python venv" >&2
            echo "   Run: python3 -m venv venv && source venv/bin/activate" >&2
            exit 1  # BLOCK execution
        fi
    fi
fi

# Node.js projects: Check node_modules
if [[ -f "$REPO_ROOT/package.json" ]]; then
    echo "📦 Node.js project detected - checking dependencies..."
    if [[ ! -d "$REPO_ROOT/node_modules" ]]; then
        echo "⚠️  WARNING: node_modules not found" >&2
        echo "   Consider running: npm install" >&2
        # Exit 2 = warning only, don't block
        exit 2
    else
        echo "✅ Node.js dependencies installed"
    fi
fi

# Rust projects: Check cargo
if [[ -f "$REPO_ROOT/Cargo.toml" ]]; then
    echo "🦀 Rust project detected - checking cargo..."
    if ! command -v cargo >/dev/null 2>&1; then
        echo "❌ ERROR: cargo not found" >&2
        echo "   Install Rust: https://rustup.rs/" >&2
        exit 1  # BLOCK execution
    else
        echo "✅ Cargo available ($(cargo --version))"
    fi
fi

#============================================================================
# 3. Project-Specific Custom Checks (Add Your Own)
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
# 4. Success
#============================================================================

echo "✅ Pre-execution checks complete - proceeding with agent execution"
exit 0
```

---

### 3. Optional: YAML Configuration System

**File**: `.specify/config/pre-check.yaml` (optional advanced feature)

```yaml
---
# Optional: Configure pre-execution checks via YAML
# If this file doesn't exist, pre-agent-check.sh uses built-in defaults

constitution:
  enabled: true
  display_reminders: true
  file: ".specify/memory/constitution.md"
  reminder_script: ".specify/scripts/bash/show-constitution-reminders.sh"

environment_checks:
  python:
    enabled: true
    blocking: true  # Exit 1 if check fails
    auto_activate_venv: true
    venv_path: "venv"
    verification_script: ".specify/scripts/bash/verify-venv.sh"
  
  node:
    enabled: true
    blocking: false  # Exit 2 (warn only) if check fails
    check_node_modules: true
    node_version_required: ">=18.0.0"
  
  rust:
    enabled: false
    blocking: true
    check_cargo: true
  
  git:
    enabled: true
    blocking: false
    check_branch_naming: true
    branch_pattern: "^[0-9]+-[a-z-]+$"

custom_checks:
  - name: "Database connection"
    command: "nc -z localhost 5432"
    blocking: false
    error_message: "PostgreSQL not running on localhost:5432"
  
  - name: "Docker daemon"
    command: "docker info >/dev/null 2>&1"
    blocking: false
    error_message: "Docker daemon not running"

session_initialization:
  offer_full_init: true
  init_script: ".specify/scripts/bash/init-agent-session.sh"
  message: "TIP: Run 'source {init_script}' for full session initialization"
```

---

## Benefits

### For Project Maintainers

✅ **Constitution Compliance**: Automatic reminder display before every agent execution
✅ **Environment Validation**: Catch missing venv, deps, tools BEFORE work starts
✅ **Auto-Fixing**: Can activate venv, install deps, fix common issues automatically
✅ **Configurable**: YAML config for complex projects, bash script for simple ones
✅ **Maintainable**: All project requirements in ONE place (`.specify/scripts/bash/pre-agent-check.sh`)

### For SpecKit Framework

✅ **Language-Agnostic**: Works for Python, Node, Rust, Go, Java, C++, etc.
✅ **Backward Compatible**: Existing projects work unchanged (opt-in via script existence)
✅ **Non-Breaking**: No changes to existing SpecKit workflows
✅ **Extensible**: Projects can add custom checks without modifying SpecKit
✅ **Best Practice**: Encourages projects to document requirements in executable form

### For AI Agents

✅ **Clear Requirements**: See constitution reminders BEFORE starting work
✅ **Early Failure**: Environment issues caught in Step 0, not during implementation
✅ **Actionable Errors**: Pre-check script provides clear fix instructions
✅ **Consistent Experience**: Same validation flow across all SpecKit agents

---

## Migration Path for Existing Projects

### Current State (This Project)

- ❌ Hardcoded venv check in `speckit.implement.agent.md` Step 1
- ❌ Constitution reminders in separate script, not automatically shown
- ❌ Project-specific logic mixed with SpecKit agent logic

### After Migration

1. Create `.specify/scripts/bash/pre-agent-check.sh` (using template above)
2. **Remove hardcoded venv check from `speckit.implement.agent.md`** (move to pre-check)
3. Move all project-specific validation to pre-check script
4. Update SpecKit agents to include Step 0 (when upstream accepts)

### Zero Breaking Changes

- If a project doesn't have `pre-agent-check.sh`, agents work exactly as before
- Existing SpecKit workflows unaffected
- Gradual migration path for projects

---

## Example Usage Scenarios

### Scenario 1: Python Project (This Project)

**Pre-Check Flow**:
1. Agent calls `pre-agent-check.sh`
2. Script detects Python files in `source/`
3. Checks if venv active, auto-activates if not
4. Displays constitution reminders
5. Exits 0 → Agent proceeds to Step 1

### Scenario 2: Node.js + Docker Project

**Pre-Check Flow**:
1. Detects `package.json`
2. Checks `node_modules` exists (warn if missing)
3. Checks Docker daemon running (warn if not)
4. Displays constitution reminders
5. Exits 2 (warning) → Agent displays warnings, proceeds

### Scenario 3: Rust Project with Database

**Pre-Check Flow**:
1. Detects `Cargo.toml`
2. Checks `cargo` command available (block if missing)
3. Checks PostgreSQL connection (warn if unavailable)
4. Displays constitution reminders
5. Exits 0 or 1 → Agent proceeds or blocks

---

## Implementation Checklist

### Phase 1: Upstream SpecKit Contribution

- [ ] Draft GitHub issue for SpecKit repository
- [ ] Propose Step 0 addition to agent outlines
- [ ] Provide reference implementation (`pre-agent-check.sh.template`)
- [ ] Create documentation for SpecKit best practices
- [ ] Submit PR to SpecKit repository

### Phase 2: This Project Migration

- [ ] Create `.specify/scripts/bash/pre-agent-check.sh`
- [ ] Test pre-check script in isolation
- [ ] Remove hardcoded venv check from `speckit.implement.agent.md` Step 1
- [ ] Update all SpecKit agent files to include Step 0
- [ ] Test full agent workflow with pre-check
- [ ] Document in project README

### Phase 3: Optional Enhancements

- [ ] Create YAML config parser for advanced projects
- [ ] Add example configs for common languages
- [ ] Create `.specify/scripts/bash/pre-check-validator.sh` (validate YAML config)
- [ ] Add pre-check script generator command

---

## Questions for Discussion

1. **Exit Code Convention**: Should we stick with 0/1/2 or add more granularity (3=info, 4=debug)?

2. **YAML Config**: Is YAML overkill? Or valuable for complex projects with many checks?

3. **Naming**: `pre-agent-check.sh` vs `agent-init.sh` vs `constitution-check.sh`?

4. **Placement**: `.specify/scripts/bash/` vs `.specify/hooks/`?

5. **SpecKit Integration**: Should SpecKit provide default templates in `.specify/templates/`?

6. **Performance**: Any concerns about adding Step 0 to ALL agents (even non-implementation)?

7. **Alternative Approaches**: Could this be done via SpecKit config instead of bash script?

---

## Alternative Approaches Considered

### Alternative 1: Agent-Specific Checks

**Idea**: Add pre-checks only to `speckit.implement.agent.md`, not all agents

**Pros**: Less overhead for planning/specification agents
**Cons**: Inconsistent experience, constitution reminders not shown during planning

**Decision**: Rejected - constitution applies to ALL work, not just implementation

### Alternative 2: SpecKit Config File

**Idea**: Add `constitution_file` and `pre_checks` to `.specify/config.yaml`

**Pros**: More structured, easier to parse
**Cons**: Less flexible, requires SpecKit to understand every check type

**Decision**: Maybe in addition to bash script, not instead of

### Alternative 3: Git Hooks

**Idea**: Use git pre-commit hooks to validate environment

**Pros**: Standard git mechanism
**Cons**: Only runs on commit, not when agent starts; agents may bypass git

**Decision**: Complementary, not a replacement

---

## Success Criteria

### For Upstream Adoption

✅ SpecKit maintainers approve the approach
✅ Step 0 added to all agent outlines
✅ Template provided in SpecKit repository
✅ Documentation added to SpecKit best practices

### For This Project

✅ All project-specific logic moved to `pre-agent-check.sh`
✅ `speckit.implement.agent.md` has no hardcoded Python/venv logic
✅ Constitution reminders displayed automatically
✅ 100% venv activation compliance (tested over 10 sessions)
✅ Zero environment-related agent failures

### For Community

✅ 3+ other projects adopt pre-execution hook pattern
✅ Examples published for Python, Node, Rust, Go
✅ Positive feedback from SpecKit community

---

## Next Steps

1. **Review this proposal** - Discuss with team/community
2. **Refine design** - Based on feedback
3. **Create GitHub issue** - Draft issue for SpecKit repository
4. **Prototype implementation** - Test in this project first
5. **Submit PR** - Contribute to SpecKit upstream
6. **Document learnings** - Share with community

---

## References

- **This Project**: Constitution Critical Reminder #1 (venv activation)
- **SpecKit Agents**: `.github/agents/speckit.*.agent.md`
- **Current Workaround**: Hardcoded venv check in `speckit.implement.agent.md` Step 1
- **Bash Script Implementation**: `.specify/scripts/bash/auto-activate-venv.sh`
- **Constitution**: `.specify/memory/constitution.md`

---

**Status**: DRAFT - Ready for review and discussion
**Next Action**: Review → Refine → Create SpecKit GitHub issue
**Estimated Effort**: 8-12 hours (prototype + PR + documentation)

---

**Last Updated**: 2025-11-21  
**Author**: Home Temperature Monitoring Project
**License**: MIT (for SpecKit contribution)
