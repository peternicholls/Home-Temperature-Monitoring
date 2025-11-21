# AI Toolkit Extension - Project Notes

**Status**: ✅ DISABLED (Confirmed 2025-11-21)  
**Disabled By**: User  
**Reason**: Confirmed interference with project-specific agent instructions

---

## Issue Observed

AI Toolkit extension may cause agents to:
- Reference global instructions (`~/.aitk/instructions/tools.instructions.md`) over project-local ones
- Skip critical project requirements (Python venv activation)
- Override project-specific instruction files

**Symptom**: Agent runs `pytest` without activating venv → `ModuleNotFoundError: No module named 'phue'`

---

## Solution

**Disable AI Toolkit extension** and rely on:
- Native AI agents (GitHub Copilot, Cursor, etc.)
- Project instruction files (`.cursorrules`, `.github/agents/copilot-instructions.md`)
- Bash automation scripts (`init-agent-session.sh`, `check-venv.sh`)

---

## If Re-enabling AI Toolkit

Before re-enabling, verify:

1. **Instruction Precedence**:
   - Confirm `.aitk/instructions/project.instructions.md` overrides global instructions
   - Test with: Create new agent session, check if it sees venv requirement

2. **Venv Activation Test**:
   ```bash
   # Deactivate venv
   deactivate
   
   # Ask agent to run tests
   # Agent SHOULD activate venv first before pytest
   
   # Verify behavior
   ```

3. **Settings Configuration**:
   - Check VS Code workspace settings (`.vscode/settings.json`)
   - Ensure AI Toolkit uses project-local instructions
   - Configure extension to respect local instruction hierarchy

4. **Fallback Plan**:
   - If issues persist, keep extension disabled
   - Project bash scripts provide equivalent functionality

---

## Current Agent Setup (Without AI Toolkit)

**Instruction Files**:
- `.cursorrules` - Cursor AI rules
- `.github/agents/copilot-instructions.md` - GitHub Copilot instructions
- `.aitk/instructions/project.instructions.md` - Available if AI Toolkit re-enabled

**Automation Scripts**:
- `.specify/scripts/bash/init-agent-session.sh` - Full session initialization
- `.specify/scripts/bash/check-venv.sh` - Quick venv status check
- `.specify/scripts/bash/auto-activate-venv.sh` - Auto venv activation
- `.specify/scripts/bash/verify-venv.sh` - Venv verification for scripts

**Expected Agent Workflow**:
1. Agent reads `.cursorrules` or `.github/agents/copilot-instructions.md`
2. Sees critical venv requirement at top
3. Runs `check-venv.sh` or `source venv/bin/activate`
4. Verifies with `which python`
5. Proceeds with Python commands

---

## Monitoring

✅ **Extension Disabled**: 2025-11-21

Monitor over next 5 agent sessions:
- [ ] Does agent activate venv before pytest?
- [ ] Does agent see project instructions?
- [ ] Are there any functionality regressions?
- [ ] Does agent reference correct instruction files?
- [ ] Venv activation compliance rate?

**Next Test**: Ask agent to run all tests and observe if it activates venv first.

**Test Command**:
```bash
# Agent should run this sequence:
.specify/scripts/bash/check-venv.sh  # Check status
source venv/bin/activate              # Activate if needed
pytest --maxfail=10 --disable-warnings -v  # Run tests
```

---

**Decision Status**: ✅ IMPLEMENTED  
**Review Date**: After next 5 agent sessions  
**Success Criteria**: 100% venv activation compliance without manual reminders
