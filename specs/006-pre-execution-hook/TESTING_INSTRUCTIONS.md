# Pre-Execution Hook Testing Instructions

## Phase 7: Agent Integration Tests

These tests require manual execution of SpecKit agents. Complete these tests to validate the pre-execution hook system.

---

### Exit Code 0 Tests (Success Path)

**T037: Test `/speckit.implement` with normal operation**

1. Ensure venv is active: `source venv/bin/activate`
2. Run: `/speckit.implement` (in agent chat)
3. **Expected behavior**:
   - Step 0 displays constitution reminders
   - venv verification shows active
   - Agent proceeds to Step 1 (check-prerequisites.sh)
   - No errors or warnings

**T038: Test `/speckit.plan` with normal operation**

1. Run: `/speckit.plan I want to build a new feature X`
2. **Expected behavior**:
   - Step 0 displays constitution reminders
   - Environment checks pass
   - Agent proceeds to Step 1
   - No errors

**T039: Test `/speckit.tasks` with normal operation**

1. Run: `/speckit.tasks`
2. **Expected behavior**:
   - Step 0 completes successfully
   - Agent proceeds to task breakdown
   - No interruptions

---

### Exit Code 1 Tests (Block Execution)

**T040-T042: Test agent blocking on critical failures**

1. **Modify pre-agent-check.sh** to force exit 1:
   ```bash
   # Add this at the end of pre-agent-check.sh (before final success message)
   echo "🚨 CRITICAL ERROR: Simulated failure for testing" >&2
   exit 1
   ```

2. **Run `/speckit.implement`**
   - **Expected**: Agent STOPS immediately
   - **Expected**: Error message displayed
   - **Expected**: Agent does NOT proceed to Step 1
   - **Expected**: No check-prerequisites.sh execution

3. **Restore pre-agent-check.sh**:
   ```bash
   # Remove the exit 1 test code
   git checkout .specify/scripts/bash/pre-agent-check.sh
   ```

---

### Exit Code 2 Tests (Warning but Proceed)

**T043-T045: Test agent warning flow**

1. **Modify pre-agent-check.sh** to force exit 2:
   ```bash
   # Add this at the end (before final success message)
   echo "⚠️  WARNING: Simulated warning for testing" >&2
   exit 2
   ```

2. **Run `/speckit.plan I want to test warnings`**
   - **Expected**: Warning message displayed
   - **Expected**: Agent CONTINUES to Step 1
   - **Expected**: Normal execution flow

3. **Restore pre-agent-check.sh**:
   ```bash
   git checkout .specify/scripts/bash/pre-agent-check.sh
   ```

---

### Backward Compatibility Test

**T046-T048: Test agents work without pre-check script**

1. **Backup and remove pre-agent-check.sh**:
   ```bash
   mv .specify/scripts/bash/pre-agent-check.sh .specify/scripts/bash/pre-agent-check.sh.bak
   ```

2. **Test all 8 agents** (one from each category):
   - `/speckit.implement` - Should skip to Step 1
   - `/speckit.plan` - Should skip to Step 1
   - `/speckit.specify` - Should skip to Step 1
   - `/speckit.tasks` - Should skip to Step 1
   - `/speckit.analyze` - Should skip to Step 1
   - `/speckit.clarify` - Should skip to Step 1
   - `/speckit.checklist` - Should skip to Step 1
   - `/speckit.constitution` - Should skip to Step 1

3. **Expected for all**: No errors, agents proceed directly to their first real step

4. **Restore pre-agent-check.sh**:
   ```bash
   mv .specify/scripts/bash/pre-agent-check.sh.bak .specify/scripts/bash/pre-agent-check.sh
   ```

---

### Real-World Scenario Tests

**T049: Test venv auto-activation**

1. **Deactivate venv**: `deactivate`
2. **Verify**: `which python` should show system Python (not venv)
3. **Run**: `/speckit.implement`
4. **Expected**: 
   - Pre-check script auto-activates venv
   - Shows "Activating virtual environment..."
   - Shows "✅ Python venv activated: .../venv"
   - Agent proceeds normally

**T050: Test fresh terminal session**

1. **Open new terminal** (fresh shell, no venv)
2. **Navigate to project**: `cd /path/to/HomeTemperatureMonitoring`
3. **Run any agent**: `/speckit.implement`
4. **Expected**:
   - Constitution reminders displayed
   - venv auto-activated
   - All environment checks pass
   - Agent execution successful

**T051: Measure session failure rate**

1. **Record baseline**: Track next 10 agent invocations
2. **Count failures**: How many fail due to:
   - Missing venv activation
   - Forgetting constitution principles
   - Environment setup issues
3. **Calculate rate**: failures / 10 = baseline rate
4. **Target**: After deployment, rate should drop to < 5%

---

## Test Results Template

```markdown
### Test Results - [Date]

**Phase 7: Agent Integration Tests**

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| T037 | Exit 0: implement | ⬜ PASS / ❌ FAIL | |
| T038 | Exit 0: plan | ⬜ PASS / ❌ FAIL | |
| T039 | Exit 0: tasks | ⬜ PASS / ❌ FAIL | |
| T040-T042 | Exit 1: Block | ⬜ PASS / ❌ FAIL | |
| T043-T045 | Exit 2: Warn | ⬜ PASS / ❌ FAIL | |
| T046-T048 | Backward Compat | ⬜ PASS / ❌ FAIL | |
| T049 | Auto-activation | ⬜ PASS / ❌ FAIL | |
| T050 | Fresh terminal | ⬜ PASS / ❌ FAIL | |
| T051 | Failure rate | ⬜ MEASURED | Baseline: __% |

**Overall Phase 7 Status**: ⬜ COMPLETE / ⏸️ IN PROGRESS / ❌ FAILED

**Notes**:
- [Add any issues, observations, or improvement ideas here]
```

---

## Success Criteria

Phase 7 is complete when:

- ✅ All exit code scenarios tested and working correctly
- ✅ Backward compatibility confirmed (agents work without pre-check)
- ✅ Real-world scenarios validated (venv auto-activation, fresh sessions)
- ✅ Session failure rate baseline recorded
- ✅ All test results documented above

**Next Step**: After Phase 7, proceed to Phase 8 (Documentation)
