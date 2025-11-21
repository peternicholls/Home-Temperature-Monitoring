# Pre-Execution Hook Troubleshooting Guide

## Quick Diagnostics

If you're experiencing issues with the pre-execution hook system, run these checks:

```bash
# 1. Verify pre-check script exists
ls -lah .specify/scripts/bash/pre-agent-check.sh

# 2. Test execution manually
bash .specify/scripts/bash/pre-agent-check.sh

# 3. Check exit code
echo $?  # Should be 0, 1, or 2

# 4. Test helper scripts
bash .specify/scripts/bash/show-constitution-reminders.sh
source .specify/scripts/bash/auto-activate-venv.sh
```

---

## Common Issues

### Issue: "pre-agent-check.sh: No such file or directory"

**Symptoms**:
- Agent fails with file not found error
- Pre-check never runs

**Diagnosis**:
```bash
# Check if file exists
ls -lah .specify/scripts/bash/pre-agent-check.sh

# Check permissions
stat .specify/scripts/bash/pre-agent-check.sh
```

**Solutions**:

1. **Script doesn't exist** → This is normal! Pre-check is optional.
   - Agents should skip to Step 1 automatically
   - If you want pre-checks, create the script:
     ```bash
     cp .specify/templates/pre-agent-check.sh.template .specify/scripts/bash/pre-agent-check.sh
     chmod +x .specify/scripts/bash/pre-agent-check.sh
     ```

2. **Script exists but not executable**:
   ```bash
   chmod +x .specify/scripts/bash/pre-agent-check.sh
   ```

3. **Wrong path** → Verify from repo root:
   ```bash
   pwd  # Should be at repo root
   find . -name "pre-agent-check.sh"
   ```

---

### Issue: Agent ignores pre-check results

**Symptoms**:
- Pre-check runs but exit code is ignored
- Agent proceeds even on exit 1
- No constitution reminders shown

**Diagnosis**:
```bash
# Check agent file has Step 0
grep -A 10 "Pre-execution validation" .github/agents/speckit.implement.agent.md

# Verify exit code behavior
bash .specify/scripts/bash/pre-agent-check.sh
echo "Exit: $?"
```

**Solutions**:

1. **Agent file missing Step 0**:
   - Check if `.github/agents/speckit.*.agent.md` has Step 0
   - Re-run spec 006 Phase 4 tasks to add Step 0
   - Or manually add Step 0 from specification Contract 1

2. **Exit code not captured correctly**:
   - Ensure pre-check script uses `exit 0/1/2` explicitly
   - Avoid using `return` (won't work as exit code)

3. **Agent implementation changed**:
   - Verify agent's Step 0 matches this pattern:
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
     ```

---

### Issue: Python venv not activating

**Symptoms**:
- "ModuleNotFoundError" errors
- `which python` shows system Python, not venv
- Pre-check says venv activated but isn't

**Diagnosis**:
```bash
# Check if venv exists
ls -ld venv/

# Try manual activation
source venv/bin/activate
which python  # Should show .../venv/bin/python

# Test auto-activate script
source .specify/scripts/bash/auto-activate-venv.sh
which python
```

**Solutions**:

1. **venv doesn't exist**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **auto-activate-venv.sh failing**:
   ```bash
   # Debug the script
   bash -x .specify/scripts/bash/auto-activate-venv.sh
   
   # Check if sourcing works
   source .specify/scripts/bash/auto-activate-venv.sh
   echo $VIRTUAL_ENV  # Should be set
   ```

3. **Shell doesn't support sourcing**:
   - pre-agent-check.sh must be run with `bash`, not `sh`
   - Verify shebang: `#!/usr/bin/env bash`

4. **venv path wrong**:
   - Check if venv is in standard location: `./venv/`
   - Or update auto-activate-venv.sh to use correct path

---

### Issue: Constitution reminders not showing

**Symptoms**:
- Pre-check runs but no reminders displayed
- Empty output from pre-check

**Diagnosis**:
```bash
# Test reminder script directly
bash .specify/scripts/bash/show-constitution-reminders.sh

# Check constitution file exists
ls -lah .specify/memory/constitution.md

# Verify --quiet flag behavior
bash .specify/scripts/bash/show-constitution-reminders.sh --quiet
```

**Solutions**:

1. **show-constitution-reminders.sh failing**:
   ```bash
   # Run with debug mode
   bash -x .specify/scripts/bash/show-constitution-reminders.sh
   
   # Check script permissions
   chmod +x .specify/scripts/bash/show-constitution-reminders.sh
   ```

2. **Constitution file missing/malformed**:
   ```bash
   # Verify file exists and has critical reminders
   cat .specify/memory/constitution.md | grep -A 5 "Critical Reminder"
   ```

3. **Script using --quiet incorrectly**:
   - `--quiet` only suppresses header/footer
   - Critical reminders should still show
   - Check pre-agent-check.sh calls: `show-constitution-reminders.sh --quiet`

---

### Issue: Exit code 1 doesn't block agent

**Symptoms**:
- Script exits with 1
- Agent shows error but continues anyway
- Step 1 runs despite failure

**Diagnosis**:
```bash
# Manually test exit 1
(bash .specify/scripts/bash/pre-agent-check.sh; echo "Exit code: $?")

# Simulate failure
echo 'echo "FAIL" >&2; exit 1' > /tmp/test-exit1.sh
bash /tmp/test-exit1.sh
echo "Captured exit: $?"  # Should be 1
```

**Solutions**:

1. **Exit code not reaching agent**:
   - Ensure script ends with `exit 1`, not `return 1`
   - Avoid error handling that swallows exit codes (no `|| true`)

2. **Agent Step 0 missing STOP logic**:
   - Verify agent has: "Exit 1: STOP - Display stderr, error message, do not continue"
   - Agent should halt execution, not proceed

3. **Error message to wrong stream**:
   - Critical errors MUST go to stderr: `echo "Error" >&2`
   - Not stdout: `echo "Error"` (wrong)

---

### Issue: Exit code 2 blocks execution (should warn only)

**Symptoms**:
- Script exits with 2
- Agent stops instead of continuing
- Warning treated as critical failure

**Diagnosis**:
```bash
# Test exit 2 behavior
echo 'echo "WARN" >&2; exit 2' > /tmp/test-exit2.sh
bash /tmp/test-exit2.sh
echo "Captured exit: $?"  # Should be 2

# Check agent's exit 2 handling
grep -A 2 "Exit 2" .github/agents/speckit.implement.agent.md
```

**Solutions**:

1. **Agent missing exit 2 handling**:
   - Verify agent has: "Exit 2: Display stdout/stderr as warning, proceed to Step 1"
   - Agent should continue to Step 1 after warning

2. **Confusion between exit 1 and 2**:
   - Review [Exit Code Conventions](.specify/memory/pre-check-exit-codes.md)
   - Use exit 1 for critical blocks, exit 2 for warnings only

---

### Issue: Pre-check too slow (> 2 seconds)

**Symptoms**:
- Pre-check takes >2 seconds to complete
- Noticeable delay before agent starts
- Users impatient/frustrated

**Diagnosis**:
```bash
# Time the execution
time bash .specify/scripts/bash/pre-agent-check.sh

# Profile sections
bash -x .specify/scripts/bash/pre-agent-check.sh 2>&1 | grep "^+"
```

**Solutions**:

1. **Remove slow checks**:
   - Avoid network calls (DNS lookups, API pings)
   - Skip expensive file scans
   - Use fast local checks only

2. **Optimize helper scripts**:
   ```bash
   # Time each component
   time bash .specify/scripts/bash/show-constitution-reminders.sh --quiet
   time source .specify/scripts/bash/auto-activate-venv.sh
   ```

3. **Cache results** (for repeated calls):
   ```bash
   # Example: Cache venv check for 60s
   CACHE_FILE="/tmp/venv-check-cache"
   if [[ -f "$CACHE_FILE" ]] && [[ $(($(date +%s) - $(stat -f %m "$CACHE_FILE"))) -lt 60 ]]; then
       cat "$CACHE_FILE"
       exit 0
   fi
   # ... do check, save result to cache
   ```

**Target**: < 0.5 seconds for optimal UX

---

### Issue: Backward compatibility broken

**Symptoms**:
- Old projects fail with pre-check errors
- Agents require pre-check script (should be optional)
- Breaking changes for existing workflows

**Diagnosis**:
```bash
# Test without pre-check script
mv .specify/scripts/bash/pre-agent-check.sh{,.bak}
# Run any agent → should work normally

# Restore
mv .specify/scripts/bash/pre-agent-check.sh{.bak,}
```

**Solutions**:

1. **Agent missing existence check**:
   - All agents MUST check if pre-check script exists
   - Pattern: "Check if `.specify/scripts/bash/pre-agent-check.sh` exists"
   - If missing, skip to Step 1 (no error)

2. **Hardcoded requirement**:
   - Remove any code that assumes pre-check must exist
   - Pre-check is ALWAYS optional

3. **Update all 8 agent files**:
   - speckit.implement, speckit.plan, speckit.specify, speckit.tasks
   - speckit.analyze, speckit.clarify, speckit.checklist, speckit.constitution
   - All must have existence check in Step 0

---

## Testing Your Fix

After resolving an issue, run these validation tests:

```bash
# 1. Manual execution test
bash .specify/scripts/bash/pre-agent-check.sh
echo "Exit code: $?"  # Should be 0

# 2. venv activation test
deactivate 2>/dev/null
source .specify/scripts/bash/auto-activate-venv.sh
which python  # Should show venv path

# 3. Constitution reminders test
bash .specify/scripts/bash/show-constitution-reminders.sh | grep "Critical Reminder"

# 4. Exit code tests
# Temporarily add "exit 1" to pre-check → run agent → should block
# Temporarily add "exit 2" to pre-check → run agent → should warn + continue

# 5. Backward compatibility test
mv .specify/scripts/bash/pre-agent-check.sh{,.bak}
# Run agent → should work without pre-check
mv .specify/scripts/bash/pre-agent-check.sh{.bak,}
```

---

## Getting Help

If issues persist:

1. **Check specification**: `specs/006-pre-execution-hook/spec.md`
2. **Review test instructions**: `specs/006-pre-execution-hook/TESTING_INSTRUCTIONS.md`
3. **Examine template**: `.specify/templates/pre-agent-check.sh.template`
4. **Verify agent files**: `.github/agents/speckit.*.agent.md`
5. **Review exit codes**: `.specify/memory/pre-check-exit-codes.md`

**Still stuck?**
- Temporarily disable: `mv .specify/scripts/bash/pre-agent-check.sh{,.disabled}`
- File an issue with full output of diagnostic commands above
- Include: OS, shell version, project structure details
