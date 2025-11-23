---
description: "Standard process for writing phase implementation reports"
applies_to: "All sprint phases that require implementation reports"
---

# Report Writing Process

**REMINDER FOR ALL AGENTS:**
- Use concise bullet points and tables for technical changes, test results, and achievements.
- Remove repetitive explanations and avoid verbose narrative; focus on outcomes and actionable guidance.
- Eliminate redundant before/after code blocks—summarize changes unless a code example is essential.
- Lessons learned may be longer than a bullet, but use economical, direct language.
- Prefer data, metrics, and verification tables over prose.
- Only include code snippets where they clarify a non-obvious solution or pattern.
- For failures, focus on root cause, fix, and impact—avoid lengthy storytelling.
- Use status icons (✅/⚠️/❌) and bolding for clarity.
- If a section is not applicable, omit it or state "N/A".

---

**Purpose**: Codified process for creating comprehensive, consistent implementation reports that capture technical details, lessons learned, and production readiness assessment.

**When to Use**: After completing any phase of a sprint that involves implementation (not just planning/design).

---

## Steps (Summary)

1. **Filename & Template**: Create report using: `YYYY-MM-DD-spec-NNN-phase-N-brief-description-implementation-report.md`
   - Location: `docs/reports/`
   - Use script: `bash .specify/scripts/bash/write-implementation-report.sh` (preferred, interactive)
   - Or copy manually: `cp .specify/templates/report-template.md docs/reports/YYYY-MM-DD-spec-NNN-phase-N-description-implementation-report.md`
   - *NEVER* start from a blank file or old report—always use the current template.

2. **Header**: Fill frontmatter (description, sprint, phase, user_story) and header (Sprint, User Story, Date, Status).
   - Status options: 🔄 IN PROGRESS, ✅ COMPLETE, ⚠️ BLOCKED, ❌ FAILED

   - **Phase/Story Numbering for General Content**: If there is no direct mapping to a specific phase or user story, use "N/A" or "Not Applicable" for the phase or story number, and assign a number in the 900 series (e.g., 901, 902, etc.). The 900 series is reserved for general implementation report content not tied to specific phases or stories. This ensures all report sections and lessons learned are traceable and unambiguous.
   - Section headers may be adapted for clarity (e.g., "Key Lessons Learned" is valid for "Lessons Learned").
   - Recommended sections are optional; their absence should not fail validation.
   - Reports with 2 or more substantive lessons learned are valid if each is detailed and actionable.
   - The "Lessons Learned" section should be substantive (suggested: 12+ lines or 2+ detailed lessons), but quality is prioritized over length.
   - Accept "N/A" or 900-series numbers for phase/story fields without warning.

3. **Executive Summary**: 2-3 direct sentences on what was implemented, current state, and key result.

4. **Key Achievements**: Concise bullets with status icons (✅/⚠️/❌).

5. **Implementation Details**: Document test suites (file path, LOC, test classes, scenarios, pass rate), components (file changes, new functions), and supporting infrastructure. Use tables/bullets for test results, technical changes, and metrics. Only include code for non-obvious solutions (5-10 lines max).

6. **Test Results**: For each test execution, document exact command, results (✅/⚠️ N/N PASSED, N% pass rate), coverage percentage, and execution time.

7. **Failure Analysis**: For EACH category of failure (even if resolved): Root cause with technical explanation, example code showing issue, solution implemented with verification, impact rating (CRITICAL/HIGH/MEDIUM/LOW), and time taken to fix. Document challenges overcome and near-misses even if all tests pass.

8. **Requirements Verification**: Table mapping requirements from spec.md to implementation (component/function) and verification method (test name or manual check). Summary: Functional Requirements N/N met, Critical Gap status.

9. **Task Completion**: Table from tasks.md, mark all completed.

10. **Technical Decisions**: Minimum 3, maximum 7 key decisions. For each: Decision statement (1-2 sentences), Rationale including alternatives considered (2-4 sentences), Impact on implementation/architecture/performance (1-3 sentences). Focus on: architecture choices, design patterns, trade-offs, performance optimizations, security decisions, tooling.

11. **Production Readiness**: ✅ Production-Ready Features (list with verification), ⚠️ Critical Requirements (severity, status, blocker yes/no, fix effort), 🔧 Optional Improvements (severity LOW, fix effort, blocker NO, decision: deferred/planned/not needed).

12. **Lessons Learned**: Minimum 3, maximum 7. Each lesson must be **Specific** (technical details not vague), **Actionable** (clear guidance), **Transferable** (applicable to future work). Format: Title, 3-5 sentence explanation (what happened, why it matters, what to do, specific example). Will be extracted to `.specify/memory/lessons-learned.md`.
   - Good example: "File Size Matters in Tests - Small test files (<1KB) exposed edge cases that don't reflect production. Increasing to 5KB+ eliminated false positives."
   - Bad example: "Testing is important - We learned testing helps find bugs. Action: Write more tests."

13. **Code Metrics**: Table with: Files Modified (N, list main), Files Created (N, list new), Lines of Code Added (~N), Test Scenarios (N tests), Test Success Rate (N%, N/N passing), Coverage (N%, module details).

14. **Files Modified**: New Files (path, N lines, description), Modified Files (path, N→N lines, +N lines, what changed), Key Implementation Details (code snippets for novel algorithms, complex logic, patterns to reuse, tricky solutions with brief comments).

15. **Sign-Off**: Required elements: Phase status with emoji, integration test results, unit test results, functional status, production ready status, key compliance items (2-3 critical requirements), deployment clearance, 2-3 sentence final assessment, next phase preview.

16. **Metadata Footer**: Include: report generation date, report update date (if updated later), sprint identifier, phase number and total phases.
   ```markdown
   *Report generated: YYYY-MM-DD*
   *Report updated: YYYY-MM-DD (what changed)*
   *Sprint: NNN-sprint-name*
   *Phase: N of N*
   ```

17. **Self-Review**: Check for concise, outcome-focused writing, proper use of bullets/tables, and no template placeholders. Verify:
   - [ ] Filename follows convention, frontmatter complete, executive summary concise (2-3 sentences)
   - [ ] Key achievements use status indicators, test results include exact commands
   - [ ] Failure analysis includes root cause for ALL failures
   - [ ] Requirements verification table complete, tasks match tasks.md
   - [ ] Minimum 3 technical decisions, minimum 3 lessons learned (specific, actionable)
   - [ ] Code metrics complete, files modified lists all changes
   - [ ] Sign-off includes all required elements, no [PLACEHOLDERS] remaining

18. **Validate Your Report** (REQUIRED): Before signing off, always validate using:
    ```bash
    bash .specify/scripts/bash/validate-report.sh docs/reports/your-report.md
    ```
    - Fix any errors or missing sections before proceeding.
    - Only consider the report complete if validation passes (or warnings are understood and accepted).

19. **Extract Lessons Learned** (REQUIRED - CRITICAL STEP):
    - After report validation passes, run: `bash .specify/scripts/bash/extract-lessons-learned.sh`
    - Follow instructions at the top of `.specify/memory/lessons-learned.md`
    - **For each lesson**: Determine category, add under that category, include source attribution (`**Source**: Sprint NNN, Phase N`), include date (`**Date**: YYYY-MM-DD`), copy lesson content verbatim, add **Action** section if missing
    - **Update metadata**: Increment lesson count, update "Last updated", add sprint/phase to "Sprints covered"
    - **Pattern recognition**: Look for recurring themes, update "Emerging Patterns" if new pattern identified
    - Rewrite for clarity and conciseness as needed, removing duplicate content, ensuring each point is specific and actionable
    - Timestamp updates automatically when complete
    - **Why This Matters**: Lessons learned feed into future implementations, preventing repeated mistakes and capturing best practices for the team and AI agents.

20. **Update Tasks.md**: Mark completed tasks (`- [ ]` → `- [X]`), verify descriptions match implementation, add notes if implementation differed from plan.

21. **Commit & Archive**: Stage and commit all report-related changes:
   ```bash
   git add docs/reports/YYYY-MM-DD-spec-NNN-phase-N-*.md
   git add .specify/memory/lessons-learned.md
   git add specs/NNN-sprint-name/tasks.md
   git commit -m "docs(NNN): Complete Phase N implementation report

   - Document test results (N/N passing)
   - Record technical decisions
   - Extract lessons learned to central memory
   - Update task completion status

   Production ready: [YES/NO]
   Next: [What's next]"
   ```

---

**For formatting and detailed examples, see the report template and example reports linked in References section.**

---

**Quality Standards**
- Report length: Typical 400-600 lines (Minimum 300, Maximum 800)
- Writing style: Factual (state what happened), Specific (exact numbers/names), Technical (proper terminology), Actionable (lessons must have clear actions)
- Avoid vague lessons ("Testing is good"), missing metrics ("Some tests failed"), no root cause analysis, generic decisions ("Used a decorator")
- Provide specific lessons (with data/examples), exact metrics (N/N, N%), root cause analysis, specific decisions (pattern name, rationale, impact)

---

**Common Mistakes to Avoid**
- ❌ Vague lessons: "Testing is good" → ✅ "Integration tests with real component interactions provide higher confidence than heavily-mocked unit tests"
- ❌ Missing metrics: "Some tests failed" → ✅ "18/35 unit tests failing due to mock path issues (51% failure rate)"
- ❌ No root cause: "Tests didn't work" → ✅ "Unit tests patch wrong module paths - patching `source.health_check.StorageManager` instead of `source.storage.manager.StorageManager`"
- ❌ Generic decisions: "Used a decorator" → ✅ "ConfigLoader Caching Pattern - Implemented class with cached properties to prevent redundant file reads when health check runs multiple validators"

---

**References**
- Report Template: `.specify/templates/report-template.md`
- Lessons Learned: `.specify/memory/lessons-learned.md`
- Example Reports: See `docs/reports/`

---

*Process version: 1.1.0*  
*Last updated: 2025-11-22*  
*Applies to: All implementation phases in all sprints*
