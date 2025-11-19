# Tasks: System Reliability and Health Improvements

**Feature**: 003-system-reliability
**Spec**: specs/003-system-reliability/spec.md
**Plan**: specs/003-system-reliability/plan.md

---

## Phase 1: Setup

- [X] T001 Create enhanced configuration file in config/config.yaml
- [X] T002 Create health check script in source/verify_setup.py
- [X] T003 Create log directory if missing at logs/
- [X] T004 Create data directory if missing at data/

## Phase 2: Foundational

- [X] T005 Implement RotatingFileHandler setup in source/utils/logging.py
- [X] T006 Implement context manager protocol in source/storage/manager.py
- [X] T007 Add WAL mode and retry logic to DatabaseManager in source/storage/manager.py

## Phase 3: [US1] Reliable Data Collection Under Load (P1)

- [X] T008 [US1] [P] Add retry logic for database locked errors in source/storage/manager.py
- [X] T009 [US1] [P] Log all retry attempts with timing in source/storage/manager.py
- [X] T010 [US1] [P] Manual test: Run concurrent collectors and verify no data loss (tests/manual/test_concurrent.md)

## Phase 4: [US2] Fast and Efficient Data Collection (P2)

- [X] T011 [US2] Optimize Hue API calls to fetch only sensors in source/collectors/hue_collector.py
- [X] T012 [US2] Log API request metadata for performance analysis in source/collectors/hue_collector.py
- [X] T013 [US2] Manual test: Measure collection cycle duration and payload size (tests/manual/test_api_optimization.md)

## Phase 5: [US3] Controlled Log File Growth (P2)

- [X] T014 [US3] [P] Configure log rotation parameters via config/config.yaml
- [X] T015 [US3] [P] Implement automatic log rotation in source/utils/logging.py
- [X] T016 [US3] [P] Manual test: Generate logs and verify rotation (tests/manual/test_log_rotation.md)

## Phase 6: [US4] Pre-Collection System Validation (P3)

- [X] T017 [US4] Implement health check command in source/verify_setup.py
- [X] T018 [US4] Validate config, secrets, database, and Hue Bridge in source/verify_setup.py
- [X] T019 [US4] Manual test: Run health check against various system states (tests/manual/test_health_check.md)

## Final Phase: Polish & Cross-Cutting Concerns

- [X] T020 Add documentation for reliability improvements in docs/evaluation-framework.md
- [X] T021 Update quickstart and troubleshooting in specs/003-system-reliability/quickstart.md
- [X] T022 Review and clean up code comments in all modified files

---

## Dependencies

- US1 must be completed before US2, US3, and US4
- US2, US3, and US4 can be executed in parallel after US1
- Polish phase depends on completion of all user stories

---

## Parallel Execution Examples

- T008, T009, T011, T012, T014, T015, T017, T018 can be executed in parallel (different files, no direct dependencies)
- Manual tests (T010, T013, T016, T019) can be run independently after implementation tasks

---

## Implementation Strategy

- MVP: Complete all tasks for US1 (Reliable Data Collection Under Load)
- Incremental delivery: Implement each user story phase independently, validate with manual tests
- Polish phase: Finalize documentation and code quality after all user stories are complete

---

## Task Count Summary

- Total tasks: 22
- US1: 3 tasks
- US2: 3 tasks
- US3: 3 tasks
- US4: 3 tasks
- Parallel opportunities: 8 implementation tasks
- Independent test criteria: Each user story has a manual test file
- Suggested MVP scope: US1 (Reliable Data Collection Under Load)

---

## Format Validation

All tasks follow strict checklist format:
- Checkbox
- Task ID (T001, T002, ...)
- [P] marker for parallelizable tasks
- [USx] label for user story phases
- Description with exact file path
