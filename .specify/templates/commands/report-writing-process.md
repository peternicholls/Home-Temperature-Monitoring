---
description: "Standard process for writing phase implementation reports"
applies_to: "All sprint phases that require implementation reports"
---

# Report Writing Process

**Purpose**: Codified process for creating comprehensive, consistent implementation reports that capture technical details, lessons learned, and production readiness assessment.

**When to Use**: After completing any phase of a sprint that involves implementation (not just planning/design).

---

## Step 1: Determine Report Filename

**Naming Convention**: `YYYY-MM-DD-spec-NNN-phase-N-brief-description-implementation-report.md`

**Examples**:
- `2024-11-21-spec-005-phase-4-implementation-report.md`
- `2025-11-21-spec-005-phase-6-health-check-implementation-report.md`

**Location**: `docs/reports/`

**Action**:
```bash
# Navigate to reports directory
cd docs/reports/

# Create report from template
cp ../../.specify/templates/report-template.md YYYY-MM-DD-spec-NNN-phase-N-description-implementation-report.md
```

---

## Step 2: Fill Report Header

Update the frontmatter and header section:

```markdown
---
description: "Phase implementation report for Sprint NNN: Sprint Name"
sprint: "NNN-sprint-name"
phase: "N"
user_story: "USN"
---

# Phase N Implementation Report: [Feature Name]

**Sprint**: NNN-sprint-name  
**User Story**: USN - [User Story Title]  
**Date**: YYYY-MM-DD  
**Status**: [Current status with emoji]
```

**Status Options**:
- 🔄 **IN PROGRESS**: Work ongoing, report may be updated
- ✅ **COMPLETE**: All work finished, production ready
- ⚠️ **BLOCKED**: Work stopped due to blocker
- ❌ **FAILED**: Implementation abandoned/failed

---

## Step 3: Write Executive Summary

**Length**: 2-3 sentences maximum

**Content**:
- What was implemented
- Current state (complete/partial/blocked)
- Key achievement or result

**Example**:
> Successfully implemented production health check framework with comprehensive component validation, exit code management, timeout enforcement, and integration with all system components. The health check is **production-ready** with all security requirements met, as demonstrated by 14/14 passing integration tests (100% pass rate).

---

## Step 4: Document Key Achievements

**Format**: Bulleted list with status indicators

**Required Elements**:
- ✅ for completed items
- ⚠️ for partial/issues
- ❌ for failed items
- **Bold** the achievement type
- Brief description

**Example**:
```markdown
✅ **Test-Driven Development**: All tests written first (35 total: 21 unit + 14 integration)  
✅ **Security Compliance**: Credential sanitization implemented (FR-030 requirement met)  
⚠️ **Test Infrastructure**: 18/35 unit tests failing due to mock path issues (not functionality bugs)
```

---

## Step 5: Document Implementation Details

### 5a. Test Suite Information

**For each test file, capture**:
- File path and name
- Total lines of code
- Number of test classes
- Number of test scenarios
- Pass rate (N/N and percentage)

**Create table of test classes**:

| Test Class | Purpose | Status |
|------------|---------|--------|
| `TestX` | Brief description | ✅ PASS |

**Summarize test results**:
- ✅ Category 1 verified
- ✅ Category 2 verified
- ⚠️ Known issues if any

### 5b. Component Implementation

**For each major component modified/created**:
- File path
- Original size → Enhanced size (if modified)
- New functions/classes added

**For each function/class**:
1. Name with backticks
2. 2-3 bullet points of what it does
3. **Result**: Status and verification method

### 5c. Supporting Infrastructure

**Document any supporting changes**:
- Helper classes/functions
- Configuration changes
- Database schema updates
- New dependencies

Include code snippets for key implementations (5-10 lines max per snippet).

---

## Step 6: Report Test Results

**For each test execution, document**:

```markdown
### [Test Category] Execution

```bash
[exact command run]
```

**Results**:
- ✅/⚠️ N/N tests PASSED (N% pass rate)
- ⚠️ N tests FAILED (if any - why)
- 📊 Coverage: N% on `module_path` (if measured)
- ⏱️ Execution time: N seconds
```

**Required test executions**:
1. Unit tests (if applicable)
2. Integration tests (if applicable)
3. Combined test run with coverage

---

## Step 7: Failure Analysis

**For EACH category of failure** (even if resolved):

### Category N: [Failure Type] ([N] tests) - [STATUS]

**Root Cause**: Clear technical explanation

**Example**: Code snippet showing the issue

**Solution Implemented** (if fixed):
- What was done
- How it was verified
- Link to commit if applicable

**Impact**: [CRITICAL/HIGH/MEDIUM/LOW] - Why it matters

**Time Taken**: ~N minutes (if fixed)

**Even if no failures**, document:
- Challenges overcome
- Near-misses
- Issues caught in review

---

## Step 8: Verify Against Requirements

**Create table mapping requirements to implementation**:

| Requirement | Implementation | Verification |
|-------------|---------------|--------------|
| [From spec.md] | Component/function name | How verified (test name, manual check) |

**Summary**:
- **Functional Requirements**: N/N met ✅/⚠️
- **Critical Gap**: None / Description ✅/❌

---

## Step 9: Document Task Completion

**Copy from tasks.md, update status**:

| Task ID | Description | Status |
|---------|-------------|--------|
| TNNN | From tasks.md | ✅/⚠️/❌ |

**Verify all tasks marked complete in tasks.md** ✅/⚠️

---

## Step 10: Record Key Technical Decisions

**Minimum 3, maximum 7 decisions**

**For each decision**:

### N. [Decision Title]

**Decision**: What was decided (1-2 sentences)

**Rationale**: Why this was chosen, what alternatives were considered (2-4 sentences)

**Impact**: How this affected the implementation, architecture, performance, etc. (1-3 sentences)

**Focus on**:
- Architecture choices
- Design patterns used
- Trade-offs made
- Performance optimizations
- Security decisions
- Tooling choices

---

## Step 11: Production Readiness Assessment

### ✅ Production-Ready Features

**List all completed, production-ready features**:
- Feature name: Brief description and how verified

### ⚠️ Critical Requirements

**For each critical item**:

1. **[Item Name]** [✅/⚠️/❌]
   - **Severity**: CRITICAL / HIGH / MEDIUM / LOW
   - **Status**: COMPLETE / PENDING / BLOCKED
   - **Blocker**: YES / NO - explanation
   - **Fix Effort**: ~N minutes (if pending)

### 🔧 Optional Improvements

**List nice-to-have improvements**:
- **Severity**: LOW
- **Fix Effort**: ~N minutes
- **Blocker**: NO
- **Decision**: Deferred / Planned / Not needed

---

## Step 12: **CRITICAL** - Document Lessons Learned

**This section will be extracted to `.specify/memory/lessons-learned.md`**

**Requirements**:
- Minimum 3 lessons
- Maximum 7 lessons
- Each lesson must be:
  - **Specific**: Include technical details, not vague observations
  - **Actionable**: Clear guidance on what to do differently
  - **Transferable**: Applicable to future work, not just this phase

**Format for each lesson**:

### [Lesson Title - Make it Memorable]

[3-5 sentence detailed explanation covering:
- What happened (context)
- Why it matters (impact)
- What to do about it (action)
- Specific example or data point
]

**Good Examples**:
```markdown
### File Size Matters in Tests

Small test files (<1KB) exposed edge cases in Python's `RotatingFileHandler` that lose data during rotation. Production-realistic file sizes (5KB+) provide more accurate validation and eliminate false positives. In Phase 5, increasing test file size from 500 bytes to 5KB eliminated data loss issues that didn't reflect production behavior.

**Action**: Use production-realistic data sizes in tests. For file operations, use 5KB+ files. For database tests, use representative row counts. Small test data can hide critical bugs.
```

**Bad Examples** (too vague):
```markdown
### Testing is Important

We learned that testing helps find bugs early.

**Action**: Write more tests.
```

**Categories to consider**:
- Testing discoveries
- Architecture insights
- Performance findings
- Error handling patterns
- Tool/framework lessons
- Process improvements
- Security insights

---

## Step 13: Document Code Metrics

**Create metrics table**:

| Metric | Value |
|--------|-------|
| **Files Modified** | N (list main files) |
| **Files Created** | N (list new files) |
| **Lines of Code Added** | ~N lines |
| **Test Scenarios** | N tests |
| **Test Success Rate** | N% (N/N passing) |
| **Coverage** | N% (module details) |

---

## Step 14: Appendix - Files Modified

**List all files changed**:

### New Files
- `path/to/file` (N lines) - Brief description

### Modified Files
- `path/to/file` (N → N lines, +N lines) - What changed

### Key Implementation Details

**Include code snippets for**:
- Novel algorithms
- Complex logic
- Patterns to reuse
- Tricky solutions

**Format**:
```python
# Brief comment explaining what this shows
def key_function():
    # Implementation
```

---

## Step 15: Write Sign-Off Section

**Required elements**:
- Phase status with emoji
- Integration test results
- Unit test results (if applicable)
- Functional status
- Production ready status
- Key compliance items (2-3 critical requirements)
- Deployment clearance
- 2-3 sentence final assessment
- Next phase preview

**Example**:
```markdown
**Phase 6 Status**: ✅ **PRODUCTION READY**  
**Integration Tests**: ✅ 14/14 PASSING (100%)  
**Functional Status**: ✅ **FULLY OPERATIONAL**  
**Production Ready**: ✅ **YES** - All requirements met

**Security Compliance**: ✅ FR-030 credential sanitization implemented and verified  
**Deployment Clearance**: ✅ **APPROVED FOR PRODUCTION**

All functional requirements met including credential sanitization (FR-030). System is operational, secure, and ready for production deployment.

**Next Phase**: Ready to proceed to Phase 7 (final sprint tasks)
```

---

## Step 16: Add Report Metadata Footer

**Include**:
- Report generation date
- Report update date (if updated later)
- Sprint identifier
- Phase number and total phases

**Format**:
```markdown
---

*Report generated: YYYY-MM-DD*  
*Report updated: YYYY-MM-DD (what changed)*  
*Sprint: NNN-sprint-name*  
*Phase: N of N*
```

---

## Step 17: Extract Lessons Learned to Central Memory

**CRITICAL STEP - DO NOT SKIP**

After completing the report:

1. **Open** `.specify/memory/lessons-learned.md`

2. **For each lesson in your report**:
   - Determine appropriate category (Testing, Architecture, Process, etc.)
   - Add lesson under that category
   - Include source attribution: `**Source**: Sprint NNN, Phase N ([Phase Name])`
   - Include date: `**Date**: YYYY-MM-DD`
   - Copy lesson content verbatim
   - Add **Action** section if not already present

3. **Update metadata**:
   - Increment lesson count
   - Update "Last updated" date
   - Add sprint/phase to "Sprints covered"

4. **Pattern recognition**:
   - Look for recurring themes across phases/sprints
   - Update "Emerging Patterns" section if new pattern identified
   - Add to "Action Items for Constitution/Templates" if structural change needed

5. **Commit both files together**:
```bash
git add docs/reports/YYYY-MM-DD-spec-NNN-phase-N-*.md
git add .specify/memory/lessons-learned.md
git commit -m "docs(NNN): Phase N implementation report + lessons learned extraction"
```

---

## Step 18: Update Tasks.md

**Mark completed tasks**:

1. Open `specs/NNN-sprint-name/tasks.md`
2. Change `- [ ]` to `- [X]` for completed tasks
3. Verify task descriptions match what was actually done
4. Add notes if implementation differed from plan

**Commit**:
```bash
git add specs/NNN-sprint-name/tasks.md
git commit -m "docs(NNN): Mark Phase N tasks complete"
```

---

## Step 19: Self-Review Checklist

Before finalizing report, verify:

- [ ] Filename follows naming convention (YYYY-MM-DD-spec-NNN-phase-N-*.md)
- [ ] Frontmatter complete with all required fields
- [ ] Executive summary is concise (2-3 sentences)
- [ ] Key achievements use status indicators (✅/⚠️/❌)
- [ ] Test results include exact commands run
- [ ] All test executions documented with pass/fail counts
- [ ] Failure analysis includes root cause for ALL failures
- [ ] Requirements verification table complete
- [ ] Task completion table matches tasks.md
- [ ] Minimum 3 key technical decisions documented
- [ ] Production readiness assessment complete
- [ ] **Lessons learned section has 3-7 specific, actionable lessons**
- [ ] Code metrics table complete
- [ ] Files modified section lists all changed files
- [ ] Sign-off section includes all required elements
- [ ] Report metadata footer present
- [ ] **Lessons extracted to lessons-learned.md**
- [ ] Tasks.md updated
- [ ] All code snippets have proper syntax highlighting
- [ ] All tables are properly formatted
- [ ] No template placeholders remaining ([BRACKETS])

---

## Step 20: Commit and Archive

**Final commit**:
```bash
# Stage all report-related changes
git add docs/reports/YYYY-MM-DD-spec-NNN-phase-N-*.md
git add .specify/memory/lessons-learned.md
git add specs/NNN-sprint-name/tasks.md

# Commit with descriptive message
git commit -m "docs(NNN): Complete Phase N implementation report

- Document test results (N/N passing)
- Record technical decisions
- Extract lessons learned to central memory
- Update task completion status

Production ready: [YES/NO]
Next: [What's next]"
```

---

## Quality Standards

### Report Length
- Typical report: 400-600 lines
- Minimum: 300 lines (simple phases)
- Maximum: 800 lines (complex phases with extensive testing)

### Writing Style
- **Factual**: State what happened, not what should have happened
- **Specific**: Include exact numbers, file names, test names
- **Technical**: Use proper terminology, include code snippets
- **Actionable**: Lessons learned must have clear actions

### Common Mistakes to Avoid

❌ **Vague lessons**: "Testing is good"  
✅ **Specific lessons**: "Integration tests with real component interactions provide higher confidence than heavily-mocked unit tests"

❌ **Missing metrics**: "Some tests failed"  
✅ **Specific metrics**: "18/35 unit tests failing due to mock path issues (51% failure rate)"

❌ **No root cause**: "Tests didn't work"  
✅ **Root cause analysis**: "Unit tests patch wrong module paths - patching `source.health_check.StorageManager` instead of `source.storage.manager.StorageManager`"

❌ **Generic decisions**: "Used a decorator"  
✅ **Specific decisions**: "ConfigLoader Caching Pattern - Implemented class with cached properties to prevent redundant file reads when health check runs multiple validators"

---

## Templates and References

**Report Template**: `.specify/templates/report-template.md`  
**Lessons Learned**: `.specify/memory/lessons-learned.md`  
**Example Reports**:
- `docs/reports/2024-11-21-spec-005-phase-4-implementation-report.md`
- `docs/reports/2024-11-21-spec-005-phase-5-log-rotation-implementation-report.md`
- `docs/reports/2024-11-21-spec-005-phase-6-health-check-implementation-report.md`

---

## Automation Opportunities

**Future improvements**:
- [ ] Script to generate report skeleton from tasks.md
- [ ] Automated lesson extraction from report to lessons-learned.md
- [ ] Report completeness checker (validates all sections present)
- [ ] Metrics auto-population from git diff and test output
- [ ] Link validator (ensure all referenced files exist)

---

*Process version: 1.0.0*  
*Last updated: 2025-11-21*  
*Applies to: All implementation phases in all sprints*
