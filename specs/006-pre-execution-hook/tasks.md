---
description: "Task list for implementing SpecKit pre-execution hook system"
---

# Tasks: Pre-Execution Hook System Implementation

**Input**: Design documents from `/specs/006-pre-execution-hook/` and `.specify/memory/speckit-pre-execution-hook-specification-and-plan.md`
**Prerequisites**: Specification and plan documents (already created)

**Organization**: Tasks are grouped by implementation phase - local project testing first, then upstream contribution preparation.

## Critical Distinction: Local vs Template

**Two separate files serve different purposes:**

1. **`.specify/scripts/bash/pre-agent-check.sh`** (Local Implementation)
   - Project-specific for HomeTemperatureMonitoring
   - Can hardcode paths: `source/`, `.specify/memory/constitution.md`
   - Can call project-specific helper scripts: `show-constitution-reminders.sh`, `auto-activate-venv.sh`
   - Phases 1-3 create/verify this file
   - **Purpose**: Works perfectly for THIS project

2. **`.specify/templates/pre-agent-check.sh.template`** (SpecKit Template)
   - **MUST BE GENERALIZED** for any SpecKit project
   - Cannot assume specific directory structures (use detection patterns)
   - Cannot assume helper scripts exist (provide inline fallbacks)
   - Provides examples with "CUSTOMIZE THIS SECTION" markers
   - Phase 9 creates this template
   - **Purpose**: Shipped with SpecKit for all projects to customize

**Key Principle**: Local file can be specific; template MUST be general.

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)

## Path Conventions

- **Agent files**: `.github/agents/speckit.*.agent.md`
- **Scripts**: `.specify/scripts/bash/`
- **Templates**: `.specify/templates/`

---

## Phase 1: Setup (Local Project Files)

**Purpose**: Create necessary directory structure and helper scripts for pre-check system

- [X] T001 Verify `.specify/scripts/bash/` directory exists (already present)
- [X] T002 [P] Verify `.specify/scripts/bash/auto-activate-venv.sh` exists and is fit for purpose (already exists ✅)
- [X] T003 [P] Verify `.specify/scripts/bash/show-constitution-reminders.sh` exists and is fit for purpose (already exists ✅)
- [X] T004 Create `.specify/scripts/bash/pre-agent-check.sh` based on specification Contract 2 template
- [X] T005 Make pre-agent-check.sh executable: `chmod +x .specify/scripts/bash/pre-agent-check.sh`

---

## Phase 2: Pre-Check Script Validation

**Purpose**: Verify pre-check script implementation matches specification requirements

- [X] T006 Verify constitution reminders display section works correctly
- [X] T007 Verify Python venv check and auto-activation section works correctly
- [X] T008 Verify exit code documentation comments are present
- [X] T009 Verify custom project-specific checks section exists (placeholder for future)
- [X] T010 Verify success message and exit 0 at end of script
 - [X] T011 Test pre-agent-check.sh execution time (should be < 2 seconds)

---

## Phase 3: Helper Scripts Validation

**Purpose**: Verify modular helper scripts work correctly with pre-agent-check.sh

### Constitution Reminders Script

- [X] T012 Verify show-constitution-reminders.sh exists in `.specify/scripts/bash/` (already exists ✅)
- [X] T013 Verify critical reminders extraction from constitution.md works
- [X] T014 Verify formatting and display logic for reminders
- [X] T015 Verify show-constitution-reminders.sh is executable
- [X] T016 Verify --quiet flag works as expected by pre-agent-check.sh

### Venv Auto-Activation Script

- [X] T017 Verify auto-activate-venv.sh exists in `.specify/scripts/bash/` (already exists ✅)
- [X] T018 Verify venv existence check logic works
- [X] T019 Verify venv auto-activation with error handling works
- [X] T020 Verify informational messages for activation status display correctly
- [X] T021 Verify auto-activate-venv.sh is executable

---

## Phase 4: Local Agent Files Update (Step 0 Addition)

**Purpose**: Add Step 0 to all local SpecKit agent outlines for testing

**⚠️ NOTE**: These are local changes for testing. Will be reverted when SpecKit upstream merges the feature.

**Step 0 Text** (from specification Contract 1):
```markdown
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
```

- [X] T022 Add Step 0 to `.github/agents/speckit.implement.agent.md`
- [X] T023 [P] Add Step 0 to `.github/agents/speckit.plan.agent.md`
- [X] T024 [P] Add Step 0 to `.github/agents/speckit.specify.agent.md`
- [X] T025 [P] Add Step 0 to `.github/agents/speckit.tasks.agent.md`
- [X] T026 [P] Add Step 0 to `.github/agents/speckit.analyze.agent.md`
- [X] T027 [P] Add Step 0 to `.github/agents/speckit.clarify.agent.md`
- [X] T028 [P] Add Step 0 to `.github/agents/speckit.checklist.agent.md`
- [X] T029 [P] Constitution agent uses project stage detection instead of Step 0 (foundational agent)

**Design Decision**: Constitution agent does NOT use Step 0 pre-execution validation because:
- Constitution defines rules that pre-checks enforce (circular dependency)
- Often first agent run on new projects (no constitution exists yet to check)
- Meta-level foundational work, not code execution
- Instead uses "Project Stage Detection" to determine if creating or updating

---

## Phase 5: Remove Hardcoded Python Venv Check

**Purpose**: Remove Python-specific logic now handled by pre-check script

- [X] T030 Locate hardcoded Python venv check in `.github/agents/speckit.implement.agent.md` Step 1 (currently lines 16-26)
- [X] T031 Remove Python venv verification step from speckit.implement.agent.md
- [X] T032 Audit all 8 agent files for any other project-specific logic
- [X] T033 Verify no other project-specific logic remains in agent files

---

## Phase 6: Testing - Isolation Tests

**Purpose**: Test pre-check script independently before agent integration

- [X] T032 Test pre-agent-check.sh in isolation with venv active (expect exit 0)
- [X] T033 Test pre-agent-check.sh with venv deactivated (expect auto-activation or exit 1)
- [X] T034 Test show-constitution-reminders.sh displays critical reminders correctly
- [X] T035 Test auto-activate-venv.sh activates venv successfully
- [X] T036 Verify pre-check script completes in < 2 seconds (actual: 0.027s)

---

## Phase 7: Testing - Agent Integration Tests

**Purpose**: Validate Step 0 works correctly with all SpecKit agents

**⚠️ MANUAL TESTING REQUIRED**: See `TESTING_INSTRUCTIONS.md` for detailed test procedures

### Exit Code 0 Tests (Success)

- [ ] T037 Run `/speckit.implement` with venv active - verify Step 0 shows constitution, proceeds to Step 1
- [ ] T038 Run `/speckit.plan` with all checks passing - verify smooth execution
- [ ] T039 Run `/speckit.tasks` with all checks passing - verify smooth execution

### Exit Code 1 Tests (Block)

- [ ] T040 Modify pre-agent-check.sh to always exit 1 temporarily
- [ ] T041 Run `/speckit.implement` - verify agent STOPS, displays error, does NOT proceed to Step 1
- [ ] T042 Restore pre-agent-check.sh to normal

### Exit Code 2 Tests (Warn)

- [ ] T043 Modify pre-agent-check.sh to always exit 2 temporarily
- [ ] T044 Run `/speckit.plan` - verify warning displayed, agent proceeds to Step 1
- [ ] T045 Restore pre-agent-check.sh to normal

### Backward Compatibility Test

- [X] T046 Rename pre-agent-check.sh to pre-agent-check.sh.bak temporarily
- [X] T047 Verify all 8 agent files have existence checks (backward compatible)
- [X] T048 Restore pre-agent-check.sh from backup

**Note**: T047 verified via code inspection - all agents check for file existence before running

### Real-World Scenario Tests

- [ ] T049 Deactivate venv, run `/speckit.implement` - verify auto-activation works
- [ ] T050 Test with fresh terminal session (no venv) - verify constitution shown + venv activated
- [ ] T051 Measure session failure rate baseline (record current rate)

---

## Phase 8: Documentation - Local Project

**Purpose**: Document the pre-check system for this project

- [X] T052 Add "Pre-Execution Hook System" section to project README.md
- [X] T053 Document exit code conventions (0/1/2) in `.specify/memory/pre-check-exit-codes.md`
- [X] T054 Add troubleshooting guide at `.specify/memory/pre-check-troubleshooting.md`
- [X] T055 Update `.specify/memory/constitution.md` to reference pre-check system (version 2.0.3)
- [X] T056 Document isolation testing at `.specify/memory/pre-check-isolation-testing.md`

---

## Phase 9: Template Creation (For Upstream Contribution)

**Purpose**: Create generalized template for SpecKit framework

**IMPORTANT**: The template MUST be language-agnostic and project-agnostic. It provides **examples** that projects customize, not hardcoded assumptions.

- [X] T057 Create `.specify/templates/pre-agent-check.sh.template` based on specification Contract 2
- [X] T058 Generalize template to work for Python, Node.js, Rust, Go, Docker projects
- [X] T059 Add extensive comments explaining each section and customization points
- [X] T060 Add placeholder examples for Docker, database checks, environment variables (commented out)
- [X] T061 Add exit code documentation at top of template
- [X] T062 Add "CUSTOMIZE THIS SECTION" markers for all project-specific logic
 - [X] T063 Add detection patterns that work across different project layouts (src/, source/, app/, etc.)
 - [X] T064 Verify template has NO hardcoded project-specific paths
 - [X] T065 Test template generates valid bash script (syntax check)

---

## Phase 10: Upstream Contribution Preparation

**Purpose**: Prepare materials for SpecKit GitHub PR

### Documentation for SpecKit

- [ ] T063 Draft SpecKit GitHub issue describing the feature
- [ ] T064 Create `docs/pre-execution-hooks.md` documentation for SpecKit
- [ ] T065 Add "Pre-Execution Hooks" section to SpecKit README.md (draft)
- [ ] T066 Create migration guide for existing SpecKit projects
- [ ] T067 Document 5+ language/framework examples (Python, Node, Rust, Go, Docker)

### PR Content

- [ ] T068 Create feature branch `feature/pre-execution-hooks` in SpecKit fork
- [ ] T069 Copy Step 0 modifications to all 8 agent outlines in SpecKit repo
- [ ] T070 Copy `.specify/templates/pre-agent-check.sh.template` to SpecKit repo
- [ ] T071 Add documentation files to SpecKit repo
- [ ] T072 Write comprehensive PR description with rationale and examples
- [ ] T073 Add testing instructions to PR

### Testing in SpecKit Repo

- [ ] T074 Test backward compatibility in SpecKit repo (no script present)
- [ ] T075 Test with Python example project using template
- [ ] T076 Test with Node.js example project using template
- [ ] T077 Verify exit code 0/1/2 behavior in SpecKit test environment

---

## Phase 11: Validation & Monitoring

**Purpose**: Measure success and gather feedback

- [ ] T078 Monitor session failure rate for 2 weeks after implementation
- [ ] T079 Collect feedback on constitution reminder visibility
- [ ] T080 Measure pre-check script execution time (confirm < 2 seconds)
- [ ] T081 Document any issues encountered and resolutions
- [ ] T082 Verify session failure rate drops below 5% (success criteria)

---

## Phase 12: Upstream Submission & Iteration

**Purpose**: Submit to SpecKit and incorporate feedback

- [ ] T083 Submit GitHub issue to specify/SpecKit repository
- [ ] T084 Submit PR to specify/SpecKit repository
- [ ] T085 Address SpecKit maintainer review feedback
- [ ] T086 Update PR based on community comments
- [ ] T087 Merge PR into SpecKit main branch (when accepted)
- [ ] T088 Wait for SpecKit release with Step 0 feature

---

## Phase 13: Final Migration (Post-Merge)

**Purpose**: Adopt official SpecKit implementation after upstream merge

- [ ] T089 Pull latest SpecKit agent outlines with official Step 0 implementation
- [ ] T090 Replace local Step 0 modifications with official SpecKit versions
- [ ] T091 Verify pre-check script still works with official implementation
- [ ] T092 Test all 8 agents with official Step 0
- [ ] T093 Update project documentation to reference official SpecKit feature
- [ ] T094 Archive this feature branch or merge to main

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Pre-Check Script (Phase 2)**: Depends on Phase 1 completion
- **Helper Scripts (Phase 3)**: Can run in parallel with Phase 2
- **Agent Files Update (Phase 4)**: Depends on Phase 2 and 3 completion
- **Remove Hardcoded Check (Phase 5)**: Depends on Phase 4 completion
- **Testing - Isolation (Phase 6)**: Depends on Phases 2, 3 completion
- **Testing - Integration (Phase 7)**: Depends on Phases 4, 5, 6 completion
- **Documentation (Phase 8)**: Can run in parallel with Phase 7
- **Template Creation (Phase 9)**: Depends on Phase 7 success (working implementation)
- **Upstream Prep (Phase 10)**: Depends on Phases 8, 9 completion
- **Validation (Phase 11)**: Depends on Phase 7 completion, runs continuously
- **Submission (Phase 12)**: Depends on Phase 10 completion
- **Final Migration (Phase 13)**: Depends on Phase 12 PR merge (external dependency)

### Parallel Opportunities

**Phase 1 (Setup):**
- T002 and T003 can run in parallel (different helper scripts)

**Phase 4 (Agent Files):**
- T022-T028 can all run in parallel (different agent files, same Step 0 text)

**Phase 6 (Isolation Tests):**
- T034 and T035 can run in parallel (testing different helper scripts)

**Phase 7 (Exit Code Tests):**
- Can run test groups sequentially, but tests within each group quickly

**Phase 9 (Template):**
- T058-T062 can run in parallel (editing different sections of template)

**Phase 10 (Upstream Prep):**
- T063-T067 can run in parallel (creating different documentation files)
- T074-T077 can run in parallel after T073 (testing different scenarios)

---

## Implementation Strategy

### MVP First (Phases 1-7 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Pre-Check Script Implementation
3. Complete Phase 3: Helper Scripts
4. Complete Phase 4: Local Agent Updates (Step 0)
5. Complete Phase 5: Remove Hardcoded Checks
6. Complete Phase 6: Isolation Testing
7. Complete Phase 7: Integration Testing
8. **STOP and VALIDATE**: Measure impact on local workflow for 1 week

**Checkpoint**: If local testing successful, proceed to upstream contribution (Phases 8-12)

### Full Implementation (All Phases)

1. Phases 1-7: Local implementation and testing (MVP)
2. Phase 8: Document for local project
3. Phases 9-10: Prepare upstream contribution materials
4. Phase 11: Monitor and validate (parallel with other phases)
5. Phase 12: Submit and iterate with SpecKit maintainers
6. Phase 13: Adopt official version (after merge)

### Incremental Delivery Checkpoints

- ✅ **Checkpoint 1**: After Phase 3 - Helper scripts working independently
- ✅ **Checkpoint 2**: After Phase 6 - Pre-check script working in isolation
- ✅ **Checkpoint 3**: After Phase 7 - Step 0 working with all agents (LOCAL TESTING COMPLETE)
- ✅ **Checkpoint 4**: After Phase 10 - Ready for upstream submission
- ✅ **Checkpoint 5**: After Phase 12 - PR merged into SpecKit
- ✅ **Checkpoint 6**: After Phase 13 - Official version adopted

---

## Success Metrics

### Local Project Success Criteria

- [ ] Pre-check script executes in < 2 seconds
- [ ] Constitution reminders displayed on every agent execution
- [ ] Python venv auto-activation works 100% of the time
- [ ] Session failure rate due to environment issues drops from 15-20% to < 5%
- [ ] Zero agent modifications needed for project-specific requirements
- [ ] All 8 agents work correctly with Step 0

### Upstream Contribution Success Criteria

- [ ] GitHub issue created and acknowledged by SpecKit maintainers
- [ ] PR submitted with all required components (code, template, docs)
- [ ] PR review feedback addressed
- [ ] PR merged into SpecKit main branch
- [ ] Feature documented in SpecKit official documentation
- [ ] Community adoption examples shared

### Quality Metrics

- [ ] Backward compatibility verified (existing projects work unchanged)
- [ ] Template works for 5+ languages (Python, Node, Rust, Go, Docker)
- [ ] Exit code conventions consistently applied (0/1/2)
- [ ] Documentation complete with examples and troubleshooting
- [ ] No breaking changes to existing SpecKit workflows

---

## Notes

- **[P] tasks** = different files, no dependencies, can run in parallel
- Helper scripts are modular to enable reuse and testing
- Step 0 text identical across all 8 agents for consistency
- Template must be generalized, not Python-specific
- Local testing MUST succeed before upstream submission
- Phase 13 depends on external SpecKit maintainers (timeline uncertain)
- Can stop after Phase 7 if only local implementation needed
- Phases 8-12 only needed if contributing to SpecKit upstream
