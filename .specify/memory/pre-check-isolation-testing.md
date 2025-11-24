# Testing Pre-Execution Hook in Isolation

This guide explains how to test the pre-execution hook system components independently before running full agent integration tests.

## Prerequisites

```bash
# Ensure you're in the repo root
cd /Users/peternicholls/Dev/HomeTemperatureMonitoring

# Verify all scripts exist
ls -lah .specify/scripts/bash/pre-agent-check.sh
ls -lah .specify/scripts/bash/auto-activate-venv.sh
ls -lah .specify/scripts/bash/show-constitution-reminders.sh
```

---

## Test 1: Constitution Reminders Display

**Purpose**: Verify critical reminders are displayed correctly

```bash
# Full display with header/footer
bash .specify/scripts/bash/show-constitution-reminders.sh

# Quiet mode (used by pre-check)
bash .specify/scripts/bash/show-constitution-reminders.sh --quiet
```

**Expected output**:
- 6 critical reminders displayed
- Numbered 1-6 with clear headings
- Quiet mode: reminders only, no banner/footer

**Pass criteria**:
- ✅ All reminders shown
- ✅ Clear formatting
- ✅ --quiet flag works

---

## Test 2: Python venv Auto-Activation

**Purpose**: Verify virtual environment activation works

```bash
# Test when venv already active
source venv/bin/activate
source .specify/scripts/bash/auto-activate-venv.sh
which python  # Should show venv path

# Test when venv inactive
deactivate 2>/dev/null
source .specify/scripts/bash/auto-activate-venv.sh
which python  # Should show venv path now
echo $VIRTUAL_ENV  # Should be set
```

**Expected behavior**:
- Detects if venv already active (skips activation)
- Activates venv if inactive
- Shows success message with Python path
- Sets $VIRTUAL_ENV environment variable

**Pass criteria**:
- ✅ Activation successful
- ✅ Python path correct: `.../venv/bin/python`
- ✅ Works from deactivated state
- ✅ Idempotent (safe to run multiple times)

**Common issues**:
- "python not found" after activation → script needs to be sourced: `source script.sh`, not `bash script.sh`
- Wrong Python path → verify venv exists: `ls -ld venv/`

---

## Test 3: Pre-Check Script - Normal Execution

**Purpose**: Test pre-check with all conditions normal

```bash
# Activate venv first
source venv/bin/activate

# Run pre-check
bash .specify/scripts/bash/pre-agent-check.sh

# Check exit code
echo "Exit code: $?"  # Should be 0
```

**Expected output**:
1. Constitution reminders displayed
2. "Python project detected" message
3. venv status check (should show active)
4. Success message: "Pre-execution checks complete"

**Pass criteria**:
- ✅ Exit code 0
- ✅ All output displayed correctly
- ✅ No errors or warnings
- ✅ Execution time < 0.5 seconds (run `time bash .specify/scripts/bash/pre-agent-check.sh`)

---

## Test 4: Pre-Check Script - venv Auto-Activation

**Purpose**: Test auto-activation when venv is not active

```bash
# Deactivate venv
deactivate 2>/dev/null

# Verify Python is system version
which python  # Should NOT show venv path

# Run pre-check
bash .specify/scripts/bash/pre-agent-check.sh

# After pre-check, verify activation (in same shell)
source .specify/scripts/bash/auto-activate-venv.sh
which python  # Should now show venv path
```

**Expected output**:
1. Constitution reminders
2. "Python project detected" message
3. "Activating virtual environment..." message
4. "✅ Python venv activated: .../venv"
5. Success with exit code 0

**Pass criteria**:
- ✅ Auto-activation triggered
- ✅ venv path shown correctly
- ✅ Exit code 0
- ✅ Works even if venv was not active

---

## Test 5: Pre-Check Performance

**Purpose**: Ensure pre-check completes quickly (<2 seconds, ideally <0.5s)

```bash
# Time the execution
time bash .specify/scripts/bash/pre-agent-check.sh

# Run multiple times for average
for i in {1..5}; do
  time bash .specify/scripts/bash/pre-agent-check.sh >/dev/null 2>&1
done
```

**Expected timing**:
- **Target**: < 0.5 seconds
- **Acceptable**: < 2 seconds
- **Unacceptable**: > 2 seconds (investigate slow operations)

**Pass criteria**:
- ✅ Average time < 0.5 seconds
- ✅ No noticeable delay to user
- ✅ Consistent timing across runs

**If slow**:
- Check for network calls (DNS, API pings)
- Remove expensive file scans
- Simplify logic in helper scripts

---

## Test 6: Exit Code 0 (Success)

**Purpose**: Verify success exit code when all checks pass

```bash
# Ensure good state
source venv/bin/activate

# Run and capture exit code
bash .specify/scripts/bash/pre-agent-check.sh
EXIT_CODE=$?

# Verify
echo "Exit code: $EXIT_CODE"
test $EXIT_CODE -eq 0 && echo "✅ PASS: Exit 0" || echo "❌ FAIL: Expected 0, got $EXIT_CODE"
```

**Pass criteria**:
- ✅ Exit code exactly 0
- ✅ Success message displayed
- ✅ No errors to stderr

---

## Test 7: Exit Code 1 (Block) - Simulated Failure

**Purpose**: Verify blocking behavior on critical failures

```bash
# Backup original script
cp .specify/scripts/bash/pre-agent-check.sh .specify/scripts/bash/pre-agent-check.sh.bak

# Add test failure before final exit 0
sed -i.tmp '/^exit 0$/i\
echo "🚨 TEST FAILURE: Simulated critical error" >&2\
exit 1
' .specify/scripts/bash/pre-agent-check.sh

# Test exit code
bash .specify/scripts/bash/pre-agent-check.sh 2>&1
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE"

# Verify
test $EXIT_CODE -eq 1 && echo "✅ PASS: Exit 1" || echo "❌ FAIL: Expected 1, got $EXIT_CODE"

# Restore original
mv .specify/scripts/bash/pre-agent-check.sh.bak .specify/scripts/bash/pre-agent-check.sh
```

**Pass criteria**:
- ✅ Exit code exactly 1
- ✅ Error message to stderr
- ✅ Agent would block execution (verify in agent test)

---

## Test 8: Exit Code 2 (Warning) - Simulated Warning

**Purpose**: Verify warning behavior on non-critical issues

```bash
# Backup original
cp .specify/scripts/bash/pre-agent-check.sh .specify/scripts/bash/pre-agent-check.sh.bak

# Add test warning before final exit 0
sed -i.tmp '/^exit 0$/i\
echo "⚠️  TEST WARNING: Simulated non-critical issue" >&2\
exit 2
' .specify/scripts/bash/pre-agent-check.sh

# Test exit code
bash .specify/scripts/bash/pre-agent-check.sh 2>&1
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE"

# Verify
test $EXIT_CODE -eq 2 && echo "✅ PASS: Exit 2" || echo "❌ FAIL: Expected 2, got $EXIT_CODE"

# Restore original
mv .specify/scripts/bash/pre-agent-check.sh.bak .specify/scripts/bash/pre-agent-check.sh
```

**Pass criteria**:
- ✅ Exit code exactly 2
- ✅ Warning message to stderr
- ✅ Agent would continue execution (verify in agent test)

---

## Test 9: File Not Found - Backward Compatibility

**Purpose**: Verify agents work when pre-check script doesn't exist

```bash
# Rename script to simulate missing
mv .specify/scripts/bash/pre-agent-check.sh .specify/scripts/bash/pre-agent-check.sh.bak

# Verify file doesn't exist
ls -lah .specify/scripts/bash/pre-agent-check.sh  # Should fail

# Restore
mv .specify/scripts/bash/pre-agent-check.sh.bak .specify/scripts/bash/pre-agent-check.sh
```

**Expected behavior** (when running agents):
- Agent checks if file exists
- If missing, skips to Step 1
- No errors or failures

**Pass criteria**:
- ✅ Agents work without pre-check script
- ✅ No "file not found" errors
- ✅ Direct execution of agent logic

**Note**: This test requires running actual agents (see TESTING_INSTRUCTIONS.md Phase 7)

---

## Test 10: Cross-Shell Compatibility

**Purpose**: Verify scripts work in different shell environments

```bash
# Test in bash (default)
bash .specify/scripts/bash/pre-agent-check.sh
echo "Bash exit: $?"

# Test in zsh (if available)
zsh .specify/scripts/bash/pre-agent-check.sh 2>/dev/null
echo "Zsh exit: $?"

# Test in sh (POSIX)
sh .specify/scripts/bash/pre-agent-check.sh 2>/dev/null
echo "Sh exit: $?"
```

**Expected**:
- Bash: Full support (target shell)
- Zsh: Should work (common on macOS)
- Sh: May fail (uses bash-specific features)

**Pass criteria**:
- ✅ Works in bash
- ✅ Works in zsh (macOS default)
- ⚠️ Sh compatibility optional (not required)

---

## Test Summary Template

```markdown
## Isolation Test Results - [Date]

| Test | Description | Status | Notes |
|------|-------------|--------|-------|
| 1 | Constitution reminders | ⬜ PASS / ❌ FAIL | |
| 2 | venv auto-activation | ⬜ PASS / ❌ FAIL | |
| 3 | Pre-check normal | ⬜ PASS / ❌ FAIL | |
| 4 | Pre-check auto-activate | ⬜ PASS / ❌ FAIL | |
| 5 | Performance (< 0.5s) | ⬜ PASS / ❌ FAIL | Actual: ___s |
| 6 | Exit code 0 | ⬜ PASS / ❌ FAIL | |
| 7 | Exit code 1 (block) | ⬜ PASS / ❌ FAIL | |
| 8 | Exit code 2 (warn) | ⬜ PASS / ❌ FAIL | |
| 9 | Backward compat | ⬜ PASS / ❌ FAIL | |
| 10 | Cross-shell | ⬜ PASS / ❌ FAIL | |

**Overall Status**: ⬜ ALL PASS / ⏸️ IN PROGRESS / ❌ FAILURES

**Next Step**: If all pass, proceed to Phase 7 (Agent Integration Tests)
```

---

## Troubleshooting

If any test fails, see:
- `.specify/memory/pre-check-troubleshooting.md` - Detailed troubleshooting guide
- `.specify/memory/pre-check-exit-codes.md` - Exit code conventions
- `specs/006-pre-execution-hook/spec.md` - Full specification

**Quick fixes**:
- Permission denied → `chmod +x .specify/scripts/bash/*.sh`
- File not found → Verify path from repo root
- venv not activating → Source script: `source script.sh`, not `bash script.sh`
- Slow execution → Remove network calls, use local checks only
