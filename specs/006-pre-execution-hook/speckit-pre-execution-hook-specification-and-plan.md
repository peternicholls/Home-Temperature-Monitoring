---
description: "Specification and implementation plan for SpecKit pre-execution hook system"
date: "2025-11-21"
status: "DRAFT - Ready for SpecKit contribution"
author: "Home Temperature Monitoring Project"
target: "specify/SpecKit upstream contribution"
feature-type: "Framework Enhancement"
---

# SpecKit Pre-Execution Hook System

## Feature Specification

### Feature Overview

Add a standardized pre-execution hook system to all SpecKit agents that allows projects to inject custom validation, environment checks, and constitution reminders before agent execution begins.

### Problem Statement

**Current Issues:**

1. **No standardized way to enforce project requirements** - Critical reminders documented in constitution files but not automatically shown to agents
2. **Project-specific hacks scattered across agent files** - Python venv checks hardcoded in `speckit.implement.agent.md`, non-portable across SpecKit updates
3. **Language-specific logic in generic agents** - Makes agents non-generalizable across Python, Node.js, Rust, Go projects
4. **High session failure rate** - 15-20% of agent sessions fail due to missing environment setup (venv not activated, dependencies not installed)

**User Impact:**

- Developers waste time debugging environment issues that could be caught before work starts
- AI agents forget critical requirements even when documented
- Project maintainers must modify SpecKit agent files to add checks (lost on updates)
- No consistent mechanism for "pre-flight checks" across different project types

### Feature Description

A **Step 0** added to all SpecKit agent outlines that:

1. Checks if `.specify/scripts/bash/pre-agent-check.sh` exists
2. If exists, runs the script before proceeding to existing agent workflow
3. Interprets exit codes:
   - `0` = All checks passed, proceed
   - `1` = Critical failure, BLOCK execution
   - `2` = Warning only, display message but proceed
4. Allows projects to inject:
   - Constitution reminder display
   - Environment validation (Python venv, Node modules, Docker daemon)
   - Auto-fixing capabilities (activate venv, install dependencies)
   - Custom project-specific checks

### User Scenarios & Testing

#### Scenario 1: Python Developer Starting Implementation

**Given:** Python project with venv requirement in constitution
**When:** Developer runs `/speckit.implement`
**Then:**
1. Agent runs `.specify/scripts/bash/pre-agent-check.sh`
2. Script displays constitution reminders
3. Script checks if venv active
4. If not active: Script auto-activates venv
5. Script exits 0
6. Agent proceeds to Step 1 with venv activated

**Success:** Developer never sees `ModuleNotFoundError`, work proceeds smoothly

#### Scenario 2: Node.js Developer Missing Dependencies

**Given:** Node.js project with `package.json` but no `node_modules/`
**When:** Developer runs `/speckit.plan`
**Then:**
1. Agent runs pre-agent-check.sh
2. Script detects missing `node_modules/`
3. Script exits 2 (warning)
4. Agent displays: "⚠️ WARNING: node_modules/ not found. Run 'npm install' first."
5. Agent proceeds to planning (non-blocking)

**Success:** Developer aware of missing deps, can decide to continue planning or fix first

#### Scenario 3: Legacy Project Without Pre-Check Script

**Given:** Existing SpecKit project without `.specify/scripts/bash/pre-agent-check.sh`
**When:** Developer runs any SpecKit agent
**Then:**
1. Agent checks for pre-agent-check.sh
2. File doesn't exist
3. Agent skips Step 0, proceeds to Step 1 immediately

**Success:** Backward compatibility maintained, no breaking changes

#### Scenario 4: Rust Developer with Custom Database Check

**Given:** Rust project requiring PostgreSQL connection
**When:** Developer runs `/speckit.implement`
**Then:**
1. Agent runs pre-agent-check.sh
2. Script checks `cargo` available (blocks if missing)
3. Script checks PostgreSQL connection on localhost:5432
4. If connection fails: Script exits 2 (warning only)
5. Agent displays warning, proceeds to implementation

**Success:** Developer aware of database issue, can decide to continue or fix

### Functional Requirements

1. **Hook Discovery**
   - Agent MUST check for `.specify/scripts/bash/pre-agent-check.sh` existence
   - Use absolute path resolution from repo root
   - Check MUST happen before any other agent steps

2. **Hook Execution**
   - If script exists, agent MUST execute it with bash
   - Script runs in repo root directory
   - Agent MUST capture both stdout and stderr
   - Agent MUST capture exit code

3. **Exit Code Handling**
   - Exit code 0: Proceed to Step 1 (success)
   - Exit code 1: BLOCK execution, display error message, ERROR state
   - Exit code 2: Display warning message, proceed to Step 1
   - Any other exit code: Treat as exit code 1 (block)

4. **Error Display**
   - On exit 1: Display script's stderr output to user
   - Include instruction: "Fix the issues above before proceeding"
   - Agent MUST NOT continue to Step 1

5. **Warning Display**
   - On exit 2: Display script's stdout and stderr to user
   - Prefix with "⚠️ WARNING:"
   - Agent continues to Step 1 after display

6. **Backward Compatibility**
   - If script doesn't exist: Skip Step 0 entirely, proceed to Step 1
   - No changes to existing agent behavior when script absent
   - No changes to existing SpecKit project workflows

7. **Universal Application**
   - Step 0 MUST be added to ALL SpecKit agents:
     - speckit.implement.agent.md
     - speckit.plan.agent.md
     - speckit.specify.agent.md
     - speckit.tasks.agent.md
     - speckit.analyze.agent.md
     - speckit.clarify.agent.md
     - speckit.checklist.agent.md
     - speckit.constitution.agent.md

### Success Criteria

1. **Measurable Outcomes:**
   - Session failure rate due to environment issues drops from 15-20% to <5%
   - Zero agent modifications required for project-specific requirements
   - Constitution reminders shown in 100% of agent executions (when script exists)
   - Pre-check script execution completes in <2 seconds for typical checks

2. **Quality Outcomes:**
   - Users report improved clarity on project requirements before work starts
   - Zero breaking changes to existing SpecKit projects
   - Projects can migrate to pre-check system without modifying SpecKit agents
   - Language-agnostic solution works for Python, Node, Rust, Go, Java projects

3. **Adoption Outcomes:**
   - Reference template provided in SpecKit `.specify/templates/`
   - Documentation includes examples for 5+ common languages/frameworks
   - Migration path documented for projects with existing custom checks

### Key Entities

**Pre-Check Script:**
- **Location:** `.specify/scripts/bash/pre-agent-check.sh` (project-specific)
- **Attributes:**
  - Executable: true
  - Owner: Project maintainer
  - Exit codes: 0 (success), 1 (block), 2 (warn)
- **Relationships:**
  - Invoked by: All SpecKit agents (Step 0)
  - May invoke: Other project scripts (constitution reminders, venv activation)

**Pre-Check Template:**
- **Location:** `.specify/templates/pre-agent-check.sh.template` (in SpecKit)
- **Attributes:**
  - Type: Reference implementation
  - Includes: Constitution display, Python venv check, Node modules check
- **Relationships:**
  - Used by: New projects during SpecKit initialization
  - Can be customized: Per-project requirements

**Agent Outline (Modified):**
- **Location:** `.github/agents/speckit.*.agent.md`
- **New Section:** Step 0 - Pre-Execution Validation
- **Relationships:**
  - Executes: Pre-check script if exists
  - Blocks on: Exit code 1
  - Warns on: Exit code 2
  - Proceeds to: Step 1 on exit code 0 or script not found

### Acceptance Criteria

1. **For SpecKit Framework:**
   - [ ] Step 0 added to all 8 agent outline files
   - [ ] Reference template created in `.specify/templates/`
   - [ ] Documentation updated with pre-check system explanation
   - [ ] Examples provided for Python, Node.js, Rust, Docker projects
   - [ ] Backward compatibility verified with existing projects

2. **For Projects:**
   - [ ] Can create `.specify/scripts/bash/pre-agent-check.sh` without modifying agents
   - [ ] Exit code 0: Agents proceed normally
   - [ ] Exit code 1: Agents block with error message
   - [ ] Exit code 2: Agents show warning, proceed
   - [ ] Script not present: No change to agent behavior

3. **For Users:**
   - [ ] Constitution reminders shown automatically (when script configured)
   - [ ] Environment errors caught before work starts
   - [ ] Clear error messages with fix instructions
   - [ ] No additional commands required to enable feature

### Scope

**In Scope:**
- Step 0 addition to all SpecKit agent outlines
- Reference template with common checks (Python venv, Node modules, Rust cargo)
- Documentation and examples
- Exit code convention (0/1/2)
- Backward compatibility guarantees

**Out of Scope:**
- YAML configuration system (future enhancement)
- Auto-generation of pre-check scripts
- Pre-check validator tool
- Language-specific check libraries
- Git hooks integration

### Dependencies

- SpecKit framework (target version: latest)
- Bash (required for script execution)
- Git (for repo root detection)

### Assumptions

1. Projects using SpecKit have bash available (macOS, Linux, WSL on Windows)
2. Pre-check scripts are maintained by project teams, not SpecKit
3. Projects know their own requirements (SpecKit provides template only)
4. Most checks complete quickly (<2 seconds)

### Risks & Mitigations

**Risk 1: Pre-check script has bugs, blocks all agents**
- **Mitigation:** Template includes extensive comments and error handling
- **Mitigation:** Documentation emphasizes testing script in isolation first

**Risk 2: Slow pre-check scripts delay agent startup**
- **Mitigation:** Document 2-second guideline for checks
- **Mitigation:** Recommend async checks for non-critical validations

**Risk 3: Projects over-use exit code 1, create friction**
- **Mitigation:** Documentation recommends exit 1 only for critical blockers
- **Mitigation:** Example template uses exit 2 (warnings) for most checks

---

## Implementation Plan

### Technical Context

**Technology Stack:**
- Markdown (Agent outline format)
- Bash (Pre-check script language)
- Git (Repo root detection)

**Integration Points:**
- All SpecKit agent outline files (8 files)
- SpecKit template system
- Project-specific `.specify/scripts/bash/` directory

**Unknowns:**
- None (all technical decisions resolved in proposal phase)

### Constitution Check

**Critical Reminders:**
1. ALWAYS preserve backward compatibility (existing projects must work unchanged)
2. ALWAYS use absolute paths for script execution
3. ALWAYS document exit code conventions clearly
4. NEVER modify SpecKit agents beyond adding Step 0

**Gates:**
- **Breaking Changes Gate:** MUST NOT break existing SpecKit projects
  - **Evaluation:** PASS - Script existence check ensures no impact when absent
- **Security Gate:** MUST NOT introduce command injection vulnerabilities
  - **Evaluation:** PASS - Script path is fixed, no user input interpolated
- **Performance Gate:** MUST NOT add >2 seconds to agent startup
  - **Evaluation:** PASS - Script execution is optional, projects control performance

### Phase 0: Research & Decisions

**Research Tasks:** (Already completed in proposal phase)

1. **Exit Code Conventions:**
   - **Decision:** Use 0 (success), 1 (block), 2 (warn)
   - **Rationale:** Standard Unix conventions, simple for projects to implement
   - **Alternatives:** More granular codes (3=info, 4=debug) - rejected as over-engineering

2. **Script Placement:**
   - **Decision:** `.specify/scripts/bash/pre-agent-check.sh`
   - **Rationale:** Consistent with existing SpecKit script location conventions
   - **Alternatives:** `.specify/hooks/` - rejected, not familiar to SpecKit users

3. **Agent Coverage:**
   - **Decision:** Add Step 0 to ALL agents
   - **Rationale:** Constitution applies to all work, not just implementation
   - **Alternatives:** Implementation-only - rejected, inconsistent experience

4. **Template Inclusion:**
   - **Decision:** Provide reference template in SpecKit `.specify/templates/`
   - **Rationale:** Lower barrier to adoption, shows best practices
   - **Alternatives:** No template, docs only - rejected, too high friction

**Output:** `research.md` (consolidated above)

### Phase 1: Design & Contracts

#### Data Model

**Pre-Check Script Entity:**
```yaml
PreCheckScript:
  path: ".specify/scripts/bash/pre-agent-check.sh"
  executable: true
  exit_codes:
    - code: 0
      meaning: "Success - proceed"
    - code: 1
      meaning: "Critical failure - block execution"
    - code: 2
      meaning: "Warning - display but proceed"
  outputs:
    - stream: "stdout"
      usage: "Informational messages, warnings"
    - stream: "stderr"
      usage: "Error messages on exit 1"
```

**Agent Step 0 Entity:**
```yaml
AgentStep0:
  name: "Pre-Execution Validation"
  order: 0  # Runs before all other steps
  optional: true  # Only runs if script exists
  blocking: conditional  # Blocks on exit 1
  affects_agents:
    - speckit.implement
    - speckit.plan
    - speckit.specify
    - speckit.tasks
    - speckit.analyze
    - speckit.clarify
    - speckit.checklist
    - speckit.constitution
```

#### Contracts

**Contract 1: Agent Outline Modification (All 8 agents)**

```markdown
## Outline

0. **Pre-Execution Validation** (Project-specific requirements):
   - Check if `.specify/scripts/bash/pre-agent-check.sh` exists
   - If exists:
     - Run: `bash .specify/scripts/bash/pre-agent-check.sh`
     - Capture exit code and output
     - Exit 0: Proceed to Step 1
     - Exit 1: STOP - Display stderr, error message, do not continue
     - Exit 2: Display stdout/stderr as warning, proceed to Step 1
   - If not exists: Skip to Step 1
   - **Why This Helps**: Projects can inject custom requirements (constitution reminders, environment checks, auto-fixes) without modifying SpecKit agent files

1. [Existing Step 1 content...]
   ...
```

**Contract 2: Pre-Check Script Template (SpecKit Framework)**

**File:** `.specify/templates/pre-agent-check.sh.template`

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
        bash "$SCRIPT_DIR/show-constitution-reminders.sh"
    else
        # Fallback: Show first 10 lines of constitution
        head -n 10 "$REPO_ROOT/.specify/memory/constitution.md"
    fi
    echo ""
fi

#============================================================================
# 2. Python Projects: Virtual Environment Check
#============================================================================

if [[ -d "$REPO_ROOT/source" ]] && find "$REPO_ROOT/source" -name '*.py' -print -quit 2>/dev/null | grep -q .; then
    echo "🐍 Python project detected - checking virtual environment..."
    
    if [[ -z "$VIRTUAL_ENV" ]]; then
        # Try to auto-activate
        if [[ -f "$REPO_ROOT/venv/bin/activate" ]]; then
            echo "   Activating virtual environment..."
            source "$REPO_ROOT/venv/bin/activate"
            echo "   ✅ Virtual environment activated"
        else
            echo "❌ ERROR: Python virtual environment required but not active" >&2
            echo "   Run: python3 -m venv venv && source venv/bin/activate" >&2
            exit 1  # BLOCK execution
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

echo "✅ Pre-execution checks complete - proceeding with agent execution"
exit 0
```

**Contract 3: Documentation (SpecKit README/Docs)**

**Section to Add:** "Pre-Execution Hooks"

```markdown
## Pre-Execution Hooks

SpecKit supports project-specific pre-execution validation through an optional hook system.

### How It Works

1. Create `.specify/scripts/bash/pre-agent-check.sh` in your project
2. Make it executable: `chmod +x .specify/scripts/bash/pre-agent-check.sh`
3. Return exit codes:
   - `0` - All checks passed, proceed
   - `1` - Critical failure, block agent execution
   - `2` - Warning only, display message but proceed

### When To Use

- Display constitution reminders before every agent execution
- Validate environment setup (Python venv, Node modules, Docker)
- Auto-fix common issues (activate venv, create directories)
- Enforce project-specific requirements

### Getting Started

Copy the reference template:

```bash
cp .specify/templates/pre-agent-check.sh.template .specify/scripts/bash/pre-agent-check.sh
chmod +x .specify/scripts/bash/pre-agent-check.sh
```

Customize the script for your project's needs.

### Examples

**Python Project:**
```bash
# Check and activate venv
if [[ -z "$VIRTUAL_ENV" ]]; then
    source venv/bin/activate || exit 1
fi
```

**Node.js Project:**
```bash
# Warn if dependencies missing
if [[ ! -d "node_modules" ]]; then
    echo "⚠️ Run 'npm install' first" >&2
    exit 2
fi
```

**Docker Project:**
```bash
# Block if Docker not running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker daemon not running" >&2
    exit 1
fi
```

See `.specify/templates/pre-agent-check.sh.template` for complete examples.
```

#### Quickstart Guide

**For SpecKit Contributors:**

1. **Clone SpecKit repository:**
   ```bash
   git clone https://github.com/specify/SpecKit.git
   cd SpecKit
   ```

2. **Create feature branch:**
   ```bash
   git checkout -b feature/pre-execution-hooks
   ```

3. **Modify agent outlines (8 files):**
   ```bash
   # Edit these files to add Step 0:
   .github/agents/speckit.implement.agent.md
   .github/agents/speckit.plan.agent.md
   .github/agents/speckit.specify.agent.md
   .github/agents/speckit.tasks.agent.md
   .github/agents/speckit.analyze.agent.md
   .github/agents/speckit.clarify.agent.md
   .github/agents/speckit.checklist.agent.md
   .github/agents/speckit.constitution.agent.md
   ```

4. **Create template:**
   ```bash
   touch .specify/templates/pre-agent-check.sh.template
   # Copy content from Contract 2 above
   ```

5. **Update documentation:**
   ```bash
   # Add "Pre-Execution Hooks" section to README.md
   # Add examples to docs/
   ```

6. **Test backward compatibility:**
   ```bash
   # Test with existing SpecKit project (no pre-check script)
   # Verify agents work unchanged
   ```

7. **Test with pre-check script:**
   ```bash
   # Create test project with pre-agent-check.sh
   # Test exit 0, exit 1, exit 2 scenarios
   # Verify blocking behavior on exit 1
   ```

8. **Submit PR:**
   ```bash
   git add .
   git commit -m "feat: Add pre-execution hook system (Step 0)"
   git push origin feature/pre-execution-hooks
   # Open PR on GitHub
   ```

**For Project Adopters:**

1. **Copy template to your project:**
   ```bash
   mkdir -p .specify/scripts/bash
   cp .specify/templates/pre-agent-check.sh.template .specify/scripts/bash/pre-agent-check.sh
   chmod +x .specify/scripts/bash/pre-agent-check.sh
   ```

2. **Customize for your needs:**
   ```bash
   # Edit .specify/scripts/bash/pre-agent-check.sh
   # Add/remove language-specific checks
   # Add custom validations
   ```

3. **Test in isolation:**
   ```bash
   # Test exit 0 (success)
   bash .specify/scripts/bash/pre-agent-check.sh
   echo $?  # Should be 0
   
   # Test with venv deactivated (should auto-activate or block)
   deactivate  # If Python project
   bash .specify/scripts/bash/pre-agent-check.sh
   ```

4. **Test with agents:**
   ```bash
   # Run any SpecKit agent
   /speckit.implement
   
   # Verify Step 0 runs first
   # Verify constitution reminders shown
   # Verify environment checks pass
   ```

### Phase 2: Implementation Checklist

#### Upstream SpecKit Changes

- [ ] **Agent Outlines** (8 files):
  - [ ] speckit.implement.agent.md - Add Step 0
  - [ ] speckit.plan.agent.md - Add Step 0
  - [ ] speckit.specify.agent.md - Add Step 0
  - [ ] speckit.tasks.agent.md - Add Step 0
  - [ ] speckit.analyze.agent.md - Add Step 0
  - [ ] speckit.clarify.agent.md - Add Step 0
  - [ ] speckit.checklist.agent.md - Add Step 0
  - [ ] speckit.constitution.agent.md - Add Step 0

- [ ] **Template Creation:**
  - [ ] Create `.specify/templates/pre-agent-check.sh.template`
  - [ ] Include Python venv check
  - [ ] Include Node.js modules check
  - [ ] Include Rust cargo check
  - [ ] Include Docker daemon check example (commented)
  - [ ] Include database connection check example (commented)

- [ ] **Documentation:**
  - [ ] Add "Pre-Execution Hooks" section to README.md
  - [ ] Create `docs/pre-execution-hooks.md` guide
  - [ ] Add examples for 5+ languages/frameworks
  - [ ] Document exit code conventions
  - [ ] Document migration path for existing projects

- [ ] **Testing:**
  - [ ] Test backward compatibility (no script present)
  - [ ] Test exit code 0 (proceed normally)
  - [ ] Test exit code 1 (block execution)
  - [ ] Test exit code 2 (warn and proceed)
  - [ ] Test with Python project (venv activation)
  - [ ] Test with Node.js project (modules warning)
  - [ ] Test with Rust project (cargo check)

#### This Project Migration

- [ ] **Remove Hardcoded Checks:**
  - [ ] Remove Python venv check from speckit.implement.agent.md Step 1
  - [ ] Verify no other project-specific logic in agent files

- [ ] **Adopt Pre-Check System:**
  - [ ] Already have `.specify/scripts/bash/pre-agent-check.sh` ✅
  - [ ] Test pre-check script independently
  - [ ] Verify constitution reminders display
  - [ ] Verify venv auto-activation works

- [ ] **Update Agent Files (when SpecKit merges PR):**
  - [ ] Pull latest SpecKit agent outlines with Step 0
  - [ ] Verify Step 0 runs our pre-check script
  - [ ] Test full agent workflow

- [ ] **Documentation:**
  - [ ] Document pre-check system in project README
  - [ ] Add to `.specify/memory/constitution.md` if needed
  - [ ] Update onboarding docs

### Phase 3: Validation & Testing

#### Test Scenarios

1. **Backward Compatibility Test:**
   - Remove `.specify/scripts/bash/pre-agent-check.sh` temporarily
   - Run all 8 SpecKit agents
   - **Expected:** Agents proceed directly to Step 1, no errors

2. **Exit Code 0 Test (Success):**
   - Restore pre-check script, ensure all checks pass
   - Run `/speckit.implement`
   - **Expected:** Constitution shown, venv activated, proceeds to Step 1

3. **Exit Code 1 Test (Block):**
   - Modify pre-check to always `exit 1`
   - Run `/speckit.plan`
   - **Expected:** Agent stops with error, does NOT proceed to Step 1

4. **Exit Code 2 Test (Warn):**
   - Modify pre-check to always `exit 2`
   - Run `/speckit.tasks`
   - **Expected:** Warning displayed, agent proceeds to Step 1

5. **Python Venv Test:**
   - Deactivate venv (`deactivate`)
   - Run `/speckit.implement`
   - **Expected:** Pre-check auto-activates venv, proceeds

6. **Node.js Modules Test:**
   - Temporarily remove `node_modules/` (if applicable)
   - Run `/speckit.plan`
   - **Expected:** Warning about missing modules, proceeds

#### Acceptance Criteria Validation

- [ ] All 8 agent outlines include Step 0
- [ ] Template exists and is executable
- [ ] Documentation complete with 5+ examples
- [ ] Backward compatibility verified
- [ ] Exit code 0/1/2 behavior correct
- [ ] Python venv auto-activation works
- [ ] Constitution reminders display correctly
- [ ] Session failure rate <5% (measure after 2 weeks)

### Rollout Plan

#### Stage 1: SpecKit PR Submission
1. Create GitHub issue in specify/SpecKit
2. Submit PR with agent outline changes
3. Include template and documentation
4. Address review feedback
5. Merge to SpecKit main branch

#### Stage 2: This Project Adoption
1. Wait for SpecKit release with Step 0
2. Update SpecKit agents in this project
3. Remove hardcoded venv check from speckit.implement.agent.md
4. Test full workflow
5. Monitor for issues

#### Stage 3: Community Adoption
1. Announce feature in SpecKit community
2. Share examples and best practices
3. Collect feedback and iterate
4. Consider YAML config system (Phase 4)

---

## Next Steps

1. **Review this specification:**
   - Validate requirements completeness
   - Confirm technical approach
   - Identify any missing edge cases

2. **Draft GitHub issue for SpecKit:**
   - Link to this specification
   - Summarize problem and solution
   - Request feedback from SpecKit maintainers

3. **Create reference PR:**
   - Fork SpecKit repository
   - Implement Step 0 in all agents
   - Create template file
   - Add documentation
   - Submit PR

4. **Test in this project:**
   - Use current pre-check script as test case
   - Validate exit code behavior
   - Measure impact on session success rate

5. **Iterate based on feedback:**
   - Address SpecKit maintainer comments
   - Refine template based on real-world usage
   - Update documentation with learnings

---

## Appendix: Exit Code Quick Reference

| Exit Code | Meaning | Agent Behavior | Use Case |
|-----------|---------|----------------|----------|
| `0` | Success | Proceed to Step 1 | All checks passed |
| `1` | Critical failure | BLOCK execution, show error | Missing venv, cargo not installed |
| `2` | Warning | Show warning, proceed to Step 1 | Missing node_modules, DB not running |
| Other | Treated as `1` | BLOCK execution | Script bugs, unexpected errors |

## Appendix: Language-Specific Examples

### Python
```bash
if [[ -d "source/" ]] && find source/ -name '*.py' -print -quit | grep -q .; then
    if [[ -z "$VIRTUAL_ENV" ]]; then
        source venv/bin/activate || exit 1
    fi
fi
```

### Node.js
```bash
if [[ -f "package.json" ]] && [[ ! -d "node_modules" ]]; then
    echo "⚠️ Run 'npm install' first" >&2
    exit 2
fi
```

### Rust
```bash
if [[ -f "Cargo.toml" ]] && ! command -v cargo &>/dev/null; then
    echo "❌ Install Rust: https://rustup.rs/" >&2
    exit 1
fi
```

### Go
```bash
if [[ -f "go.mod" ]] && ! command -v go &>/dev/null; then
    echo "❌ Install Go: https://go.dev/dl/" >&2
    exit 1
fi
```

### Docker
```bash
if ! docker info >/dev/null 2>&1; then
    echo "⚠️ Docker daemon not running" >&2
    exit 2
fi
```
