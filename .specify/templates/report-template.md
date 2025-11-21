---
description: "Phase implementation report template for Sprint [NNN]: [Sprint Name]"
sprint: "[NNN-sprint-name]"
phase: "[N]"
user_story: "[USN]"
---

# Phase [N] Implementation Report: [Feature Name]

**Sprint**: [NNN-sprint-name]  
**User Story**: [USN] - [User Story Title]  
**Date**: [YYYY-MM-DD]  
**Status**: [🔄 IN PROGRESS | ✅ COMPLETE | ⚠️ BLOCKED | ❌ FAILED]

---

## Executive Summary

[2-3 sentence overview of what was implemented and its current state]

### Key Achievements

[Bulleted list of major accomplishments with status indicators (✅/⚠️/❌)]
- ✅ **Achievement 1**: Description
- ✅ **Achievement 2**: Description
- ⚠️ **Issue Identified**: Description
- ✅ **Resolution Applied**: Description

---

## Implementation Details

### Test Suite (`tests/test_[feature].py`)

**Total Lines**: [N]  
**Test Classes**: [N]  
**Test Scenarios**: [N]  
**Pass Rate**: [N]/[N] ([N]%) [✅/⚠️]

#### Test Coverage Table

| Test Class | Purpose | Status |
|------------|---------|--------|
| `TestFeature1` | What it tests | ✅ PASS / ⚠️ FAIL |
| `TestFeature2` | What it tests | ✅ PASS / ⚠️ FAIL |

**Test Results Summary**:
- ✅ [Key test category 1]
- ✅ [Key test category 2]
- ⚠️ [Issue if any]

#### Unit Tests (if applicable)

**Total Lines**: [N]  
**Test Classes**: [N]  
**Test Scenarios**: [N]  
**Pass Rate**: [N]/[N] ([N]%)

[Same table structure as above]

### Component Implementation (`source/[module]/[file].py`)

**Original Size**: [N] lines  
**Enhanced Size**: [N] lines  
**New Functions/Classes**: [N]

#### Implemented Components

1. **`component_name()`**
   - Purpose/responsibility
   - Key features
   - **Result**: ✅ Functional / ⚠️ Partial / ❌ Failed

2. **`component_name_2()`**
   - Purpose/responsibility
   - Key features
   - **Result**: Status and verification

[Continue for all major components]

### Supporting Infrastructure

#### [Supporting Component 1] (`source/[path]/[file].py`)

**Added**: [What was added]

```python
# Key code snippet showing the addition
```

**Result**: ✅ Status and how verified

[Repeat for other supporting components]

---

## Test Results

### [Test Category 1] Execution

```bash
pytest [test_files] -v [flags]
```

**Results**:
- ✅ [N]/[N] tests PASSED ([N]% pass rate)
- ⚠️ [N] tests FAILED (if any - explain why)
- ⏱️ Execution time: [N] seconds

### [Test Category 2] Execution (if applicable)

[Same structure]

### Combined Test Execution

```bash
pytest [all_relevant_tests] -v --cov=[modules] --cov-report=term-missing
```

**Results**:
- ✅ [N] [category] tests PASSED
- ⚠️ [N] tests FAILED (if any)
- 📊 Coverage: [N]% on `[module_path]`
- ⏱️ Execution time: [N] seconds

---

## Failure Analysis

### Category 1: [Failure Type] ([N] tests) - [✅ FIXED / ⚠️ PENDING / ❌ BLOCKED]

**Root Cause**: [Clear explanation of why tests failed or issue occurred]

**Example**:
```python
# Show the problematic code or test
```

**Solution Implemented** (if fixed):
- [What was done to fix it]
- [How it was verified]

**Impact**: [CRITICAL / HIGH / MEDIUM / LOW] - [Explanation]

**Time Taken**: ~[N] minutes (if fixed)

[Repeat for each failure category]

---

## Verification Against Requirements

### User Story [N] Requirements

| Requirement | Implementation | Verification |
|-------------|---------------|--------------|
| [Requirement 1] | `component_name()` | ✅ Test name passes |
| [Requirement 2] | `component_name()` | ⚠️ Partial - missing [X] |
| [Requirement 3] | Implementation | ✅ How verified |

**Functional Requirements**: [N]/[N] met [✅/⚠️]  
**Critical Gap**: [None / Description of gap] [✅/❌]

---

## Task Completion

### Phase [N] Tasks (T[NNN]-T[NNN])

| Task ID | Description | Status |
|---------|-------------|--------|
| T[NNN] | [Task description] | ✅ Complete / ⚠️ Partial / ❌ Blocked |
| T[NNN] | [Task description] | Status |

**All tasks marked complete in tasks.md** ✅/⚠️

---

## Key Technical Decisions

### 1. [Decision Name]

**Decision**: [What was decided]

**Rationale**: [Why this decision was made, what alternatives were considered]

**Impact**: [How this affected the implementation, performance, architecture, etc.]

### 2. [Decision Name]

[Same structure]

[Include 3-5 key technical decisions that shaped the implementation]

---

## Production Readiness Assessment

### ✅ Production-Ready Features [All Complete / Partial]

- **Feature 1**: Description and verification
- **Feature 2**: Description and verification
- **Feature 3**: Description and verification

### ⚠️ Critical Requirements [Met / Pending / Blocked]

1. **[Requirement Name]** [✅/⚠️/❌]
   - **Severity**: CRITICAL / HIGH / MEDIUM / LOW
   - **Status**: COMPLETE / PENDING / BLOCKED
   - **Blocker**: YES / NO - explanation

[List all critical items that could block production]

### 🔧 Optional Improvements (Not Blocking)

3. **[Improvement Name]**
   - **Severity**: LOW
   - **Fix Effort**: ~[N] minutes
   - **Blocker**: NO - explanation
   - **Decision**: Deferred / Planned / Not needed

---

## Implementation Summary - [Option Name] [✅ COMPLETE / ⚠️ PARTIAL]

### Option [N]: [Option Name] - [✅ COMPLETED / ⚠️ PENDING / ❌ BLOCKED]

**Time Taken**: ~[N] minutes  
**Focus**: [What this option addressed]

**Tasks Completed**:
1. ✅ **[Task 1]**
   - [What was done]
   - Verified: [How it was verified] ✅

2. ✅ **[Task 2]**
   - [What was done]
   - Verified: [How it was verified] ✅

**Deliverable**: ✅ [Summary of what was delivered]

[Include alternative options if applicable]

---

## Lessons Learned

[CRITICAL SECTION - This content will be extracted to central memory]

1. **[Lesson Title]**: [Detailed lesson learned with context, what went wrong/right, why it matters, and what to do differently next time. Be specific with examples and technical details.]

2. **[Lesson Title]**: [Same structure - each lesson should be actionable and transferable to future work]

3. **[Lesson Title]**: [Continue with 3-7 key lessons that would help future implementations]

[Examples of good lessons learned:
- Technical discoveries (e.g., "File Size Matters: Small test files (<1KB) exposed edge cases...")
- Process improvements (e.g., "TDD Catches Edge Cases Early: Writing tests first revealed...")
- Tool/framework insights (e.g., "Mock Patch Paths Are Fragile: Python's @patch decorator must patch...")
- Architecture decisions (e.g., "Integration Tests More Valuable Than Unit Tests: Integration tests with real...")
- Performance insights (e.g., "Error Classification Is Critical: Differentiating permanent vs transient errors...")
]

---

## Code Metrics

| Metric | Value |
|--------|-------|
| **Files Modified** | [N] ([list main files]) |
| **Files Created** | [N] ([list new files]) |
| **Lines of Code Added** | ~[N] lines |
| **Test Scenarios** | [N] comprehensive tests |
| **Test Success Rate** | [N]% ([N]/[N] passing) |
| **Coverage** | [N]% ([module coverage details]) |

---

## Appendix: Files Modified

### New Files

- `[path/to/file]` ([N] lines) - [Brief description]

### Modified Files

- `[path/to/file]` ([N] → [N] lines, +[N] lines) - [What changed]

### Key Implementation Details

**[Feature Name]** (`[file_path]`):
```python
# Show key code snippets that are important for understanding
# the implementation or for future reference
```

**[Another Feature]** (`[file_path]`):
- Bullet points explaining the implementation if code snippet not needed

---

## Sign-Off

**Phase [N] Status**: [🔄 IN PROGRESS / ✅ COMPLETE / ⚠️ BLOCKED]  
**Integration Tests**: [✅/⚠️] [N]/[N] PASSING ([N]%)  
**Unit Tests**: [✅/⚠️] [N]/[N] PASSING ([N]%)  
**Functional Status**: [✅ OPERATIONAL / ⚠️ PARTIAL / ❌ BLOCKED]  
**Production Ready**: [✅ YES / ⚠️ WITH CAVEATS / ❌ NO]

**[Key Compliance Item]**: ✅/⚠️/❌ [Status and details]  
**[Key Compliance Item]**: ✅/⚠️/❌ [Status and details]  
**[Key Metric]**: [Value and interpretation]

**Deployment Clearance**: [✅ APPROVED FOR PRODUCTION / ⚠️ CONDITIONAL / ❌ BLOCKED]

[Final assessment summary - 2-3 sentences on overall state and readiness]

**Next Phase**: [What comes next, if applicable]

---

*Report generated: [YYYY-MM-DD]*  
*Report updated: [YYYY-MM-DD] ([what changed])*  
*Sprint: [NNN-sprint-name]*  
*Phase: [N] of [N]*
