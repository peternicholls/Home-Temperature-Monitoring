---
description: "Phase implementation report template for Sprint [NNN]: [Sprint Name]"
sprint: "[NNN-sprint-name]"
phase: "[N]"
user_story: "[USN]"
---


# Phase [N] Implementation Report: [Feature Name]

> **Template Guidance:**
> - Use concise bullet points and tables for technical changes, test results, and achievements.
> - Remove repetitive explanations and avoid verbose narrative; focus on outcomes and actionable guidance.
> - Eliminate redundant before/after code blocks—summarize changes unless a code example is essential.
> - Lessons learned may be longer than a bullet, but use economical, direct language.
> - Shorten narrative sections; avoid restating the same point in multiple places.
> - Prefer data, metrics, and verification tables over prose.
> - Only include code snippets where they clarify a non-obvious solution or pattern.
> - For failures, focus on root cause, fix, and impact—avoid lengthy storytelling.
> - Use status icons (✅/⚠️/❌) and bolding for clarity.
> - If a section is not applicable, omit it or state "N/A".
> - **Phase/Story Numbering for General Content**: If a report section or lesson does not map directly to a specific phase or user story, use "N/A" or "Not Applicable" for the phase or story number, and assign a number in the 900 series (e.g., 901, 902, etc.). The 900 series is reserved for general implementation report content not tied to specific phases or stories. This ensures traceability and clarity in documentation and lessons learned.
> - Section headers may be adapted for clarity (e.g., "Key Lessons Learned" is valid for "Lessons Learned").
> - Recommended sections are optional; their absence should not fail validation.
> - Reports with 2 or more substantive lessons learned are valid if each is detailed and actionable.
> - The "Lessons Learned" section should be substantive (suggested: 12+ lines or 2+ detailed lessons), but quality is prioritized over length.
> - Accept "N/A" or 900-series numbers for phase/story fields without warning.

**Sprint**: [NNN-sprint-name]  
**User Story**: [USN] - [User Story Title]  
**Date**: [YYYY-MM-DD]  
**Status**: [🔄 IN PROGRESS | ✅ COMPLETE | ⚠️ BLOCKED | ❌ FAILED]

---


## Executive Summary

[2-3 sentence overview of what was implemented and its current state. Be direct—avoid background or justification.]


### Key Achievements

[Concise bullet list of major accomplishments, issues, and resolutions. Use status icons.]

---


## Implementation Details

### Test Suite (`tests/test_[feature].py`)

| Metric | Value |
|--------|-------|
| **Total Lines** | [N] |
| **Test Classes** | [N] |
| **Test Scenarios** | [N] |
| **Pass Rate** | [N]/[N] ([N]%) [✅/⚠️] |

| Test Class | Purpose | Status |
|------------|---------|--------|
| `TestFeature1` | What it tests | ✅ PASS / ⚠️ FAIL |
| `TestFeature2` | What it tests | ✅ PASS / ⚠️ FAIL |

**Summary:**
- [List only key outcomes, issues, and resolutions.]


### Component Implementation (`source/[module]/[file].py`)

| Metric | Value |
|--------|-------|
| **Original Size** | [N] lines |
| **Enhanced Size** | [N] lines |
| **New Functions/Classes** | [N] |

| Component | Purpose | Key Features | Result |
|-----------|---------|--------------|--------|
| `component_name()` | [Purpose] | [Features] | ✅/⚠️/❌ |
| ... | ... | ... | ... |

[Summarize changes; only include code snippets for non-obvious logic.]


### Supporting Infrastructure

[List supporting changes in bullet points or a table. Only show code if it clarifies a tricky solution.]

---


## Test Results

[Use tables and bullet points for results. Only include commands and output summaries.]

| Test | Pass/Fail | Count | Coverage | Time |
|------|-----------|-------|----------|------|
| [Category] | ✅/⚠️ | [N]/[N] | [N]% | [N]s |

**Notes:**
- [Highlight only key issues or outcomes.]

---


## Failure Analysis

[For each failure, use a table or concise bullet points: Type, Root Cause, Solution, Impact. Only show code if it clarifies the fix.]

---


## Verification Against Requirements

[Use a table to map requirements to implementation and verification.]

---


## Task Completion

[Table: Task ID, Description, Status. Mark all completed in tasks.md.]

---


## Key Technical Decisions

[List 3-5 key decisions. Use bullet points or a table for clarity.]

---


## Production Readiness Assessment

[List features and requirements in concise bullet points or tables. Only elaborate if a blocker exists.]

---


## Implementation Summary

[Summarize options, tasks, and deliverables in a table or concise bullets.]

---


## Lessons Learned

[CRITICAL SECTION – Will be extracted to central memory.]

- Use economical, direct language. Each lesson should be specific, actionable, and transferable.
- Lessons can be longer than a bullet, but avoid unnecessary narrative or repetition.
- Focus on what changed, why it matters, and what to do differently next time.

---


## Code Metrics

[Use a table for all metrics.]

---


## Appendix: Files Modified

[List new/modified files in tables or bullets. Only show code for non-obvious logic.]

---


## Sign-Off

[Summarize status, test results, and readiness in concise bullets or a short table.]


---

*Report generated: YYYY-MM-DD*  
*Report updated: YYYY-MM-DD (what changed)*  
*Sprint: NNN-sprint-name*  
*Phase: N of N*

---

**Note on 900 Series Numbering:**
If this report or any section/lesson does not map directly to a specific phase or user story, use "N/A" or "Not Applicable" for the phase or story number, and assign a number in the 900 series (e.g., 901, 902, etc.). The 900 series is reserved for general implementation report content not tied to specific phases or stories.
