---
description: "Task list for Philips Hue Temperature Collection feature"
---

# Tasks: Philips Hue Temperature Collection

**Input**: Design documents from `/specs/002-hue-integration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are NOT explicitly requested in this feature specification. Following the constitution's "quick and dirty" principle and manual verification acceptance, test tasks are excluded.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project structure: `source/` (code), `config/` (configuration), `data/` (database), `logs/` (logging)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for Hue integration

- [ ] T001 Create `source/collectors/` directory for Hue integration modules
- [ ] T002 Add `phue==1.1` dependency to `requirements.txt`
- [ ] T003 [P] Copy `specs/002-hue-integration/contracts/secrets-hue.yaml.example` to `config/secrets.yaml` (if not exists)
- [ ] T004 [P] Append Hue configuration from `specs/002-hue-integration/contracts/config-hue.yaml` to `config/config.yaml`
- [ ] T005 [P] Create `logs/hue_collection.log` file (empty, for collection logs)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Execute database schema SQL from `specs/002-hue-integration/contracts/database-schema.sql` to create `temperature_readings` table (note: auto-created by code, see schema header)
- [ ] T007 [P] Add Hue config validation rules to `source/config/validator.py` for bridge_ip, auto_discover, collection_interval fields
- [ ] T008 [P] Add Hue secrets validation to `source/config/validator.py` for api_key and bridge_id fields
- [ ] T009 [P] Update `source/storage/manager.py` to include insert method for temperature readings with UNIQUE constraint handling

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Authenticate with Hue Bridge (Priority: P1) 🎯 MVP Component

**Goal**: Establish secure connection to Philips Hue Bridge to enable temperature data collection

**Independent Test**: Run authentication script, press Bridge button, verify API key and Bridge ID are stored in `config/secrets.yaml`

### Implementation for User Story 1

- [ ] T010 [P] [US1] Create `source/collectors/__init__.py` with module documentation
- [ ] T011 [US1] Implement Bridge discovery logic using `phue.discover_nupnp()` in `source/collectors/hue_auth.py` (handles DHCP IP changes)
- [ ] T012 [US1] Implement manual IP fallback from config in `source/collectors/hue_auth.py` (edge case: mDNS blocked networks)
- [ ] T013 [US1] Implement button press authentication flow using `phue.Bridge.connect()` in `source/collectors/hue_auth.py`
- [ ] T014 [US1] Add function to save API key and Bridge ID to `config/secrets.yaml` in `source/collectors/hue_auth.py`
- [ ] T015 [US1] Add CLI entry point with argparse for authentication command in `source/collectors/hue_auth.py`
- [ ] T016 [US1] Add logging for discovery attempts, button press prompt, and success/failure in `source/collectors/hue_auth.py`
- [ ] T017 [US1] Add error handling for Bridge not found, button not pressed, and authentication failures in `source/collectors/hue_auth.py`

**Checkpoint**: Authentication script can discover Bridge, authenticate via button press, and store credentials securely

---

## Phase 4: User Story 2 - Discover Temperature Sensors (Priority: P2)

**Goal**: Identify all temperature-capable Hue sensors and map them to physical locations

**Independent Test**: Run sensor discovery after authentication, verify all temperature sensors are listed with location names and device IDs

### Implementation for User Story 2

- [ ] T018 [US2] Implement sensor discovery using `bridge.get_api()['sensors']` in `source/collectors/hue_collector.py`
- [ ] T019 [US2] Filter sensors by type `ZLLTemperature` in `source/collectors/hue_collector.py`
- [ ] T020 [P] [US2] Implement location mapping function using config `sensor_locations` in `source/collectors/hue_collector.py`
- [ ] T021 [P] [US2] Add fallback to sensor name when unique_id not in config in `source/collectors/hue_collector.py`
- [ ] T022 [US2] Extract sensor metadata (unique_id, name, model_id, battery, reachable) in `source/collectors/hue_collector.py`
- [ ] T023 [US2] Add CLI option `--discover` to list all sensors with metadata in `source/collectors/hue_collector.py`
- [ ] T024 [US2] Add logging for sensor discovery results and offline sensors in `source/collectors/hue_collector.py`

**Checkpoint**: Sensor discovery lists all temperature-capable sensors with correct location mapping

---

## Phase 5: User Story 3 - Collect Temperature Readings (Priority: P1) 🎯 MVP Component

**Goal**: Read current temperature values from all discovered Hue sensors with proper timestamps and metadata

**Independent Test**: Run single collection cycle, verify temperature readings are retrieved from all available sensors with valid timestamps and correct format

### Implementation for User Story 3

- [ ] T025 [US3] Implement collection cycle function to retrieve all sensors in `source/collectors/hue_collector.py`
- [ ] T026 [P] [US3] Convert temperature from 0.01°C units to Celsius (divide by 100.0) in `source/collectors/hue_collector.py`
- [ ] T027 [P] [US3] Generate ISO 8601 timestamp with timezone using `datetime.now(timezone.utc).isoformat()` in `source/collectors/hue_collector.py`
- [ ] T028 [P] [US3] Format device_id as `hue:{sensor_unique_id}` in `source/collectors/hue_collector.py`
- [ ] T029 [P] [US3] Set device_type to `hue_sensor` for all readings in `source/collectors/hue_collector.py`
- [ ] T030 [P] [US3] Validate temperature range 0-40°C and flag anomalies in `source/collectors/hue_collector.py` (edge case: out-of-range readings)
- [ ] T031 [P] [US3] Extract battery_level from sensor config if available in `source/collectors/hue_collector.py` (edge case: low battery detection)
- [ ] T032 [P] [US3] Map signal_strength from reachable boolean (1=reachable, 0=unreachable) in `source/collectors/hue_collector.py`
- [ ] T033 [US3] Implement retry logic with exponential backoff (1s, 2s, 4s) for collection failures in `source/collectors/hue_collector.py` (edge case: malformed API data)
- [ ] T034 [US3] Handle offline sensors gracefully (skip and continue with others) in `source/collectors/hue_collector.py` (edge case: low battery/offline sensors)
- [ ] T035 [US3] Add CLI options `--collect-once` and `--continuous` in `source/collectors/hue_collector.py`
- [ ] T036 [US3] Add logging for collection start, per-sensor results, errors, and cycle completion in `source/collectors/hue_collector.py`

**Checkpoint**: Collection script successfully retrieves and formats temperature readings with all required and optional fields

---

## Phase 6: User Story 4 - Store Readings in Database (Priority: P1) 🎯 MVP Component

**Goal**: Persist temperature readings in SQLite database with proper schema and constraints

**Independent Test**: Collect readings and verify they are written to database, retrievable via queries, with all required fields populated

### Implementation for User Story 4

- [ ] T037 [US4] Add method `insert_temperature_reading()` to `source/storage/manager.py` for inserting readings
- [ ] T038 [P] [US4] Handle UNIQUE constraint violations for duplicate (device_id, timestamp) in `source/storage/manager.py` (prevents duplicate readings)
- [ ] T039 [P] [US4] Handle database locked errors with retry logic in `source/storage/manager.py` (edge case: concurrent access)
- [ ] T040 [P] [US4] Store all required fields (timestamp, device_id, temperature_celsius, location, device_type) in `source/storage/manager.py`
- [ ] T041 [P] [US4] Store optional fields (is_anomalous, battery_level, signal_strength, raw_api_response) in `source/storage/manager.py`
- [ ] T042 [US4] Call database insert from collection cycle in `source/collectors/hue_collector.py`
- [ ] T043 [US4] Add logging for successful inserts, duplicates, and database errors in `source/storage/manager.py`
- [ ] T044 [US4] Add auto-creation of database schema if table doesn't exist in `source/storage/manager.py`

**Checkpoint**: Temperature readings are successfully stored in database with proper constraints and error handling

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T045 [P] Update `specs/002-hue-integration/quickstart.md` with actual CLI commands and expected outputs
- [ ] T046 [P] Add troubleshooting section to `specs/002-hue-integration/quickstart.md` for common errors
- [ ] T047 [P] Add sample database queries to `specs/002-hue-integration/contracts/database-schema.sql` for validation
- [ ] T048 Code review and refactoring for consistency across collector modules
- [ ] T049 Run through quickstart.md validation steps to verify end-to-end functionality
- [ ] T050 [P] Update main `README.md` with Hue integration status and links

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (Authentication) should complete first as it's needed for testing others
  - US2 (Discovery) depends on US1 for credentials
  - US3 (Collection) depends on US1 for credentials and US2 for sensor info
  - US4 (Storage) can be developed in parallel with US3, integrated at T042
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - Authentication)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2 - Discovery)**: Requires US1 credentials to test, but implementation can proceed in parallel
- **User Story 3 (P1 - Collection)**: Requires US1 credentials and US2 discovery logic - integrate at runtime
- **User Story 4 (P1 - Storage)**: Can develop independently, integrates with US3 at T042

### Within Each User Story

**US1 (Authentication)**:
- T010 (init) → T011-T014 (parallel: discovery, fallback, auth, save) → T015-T017 (sequential: CLI, logging, errors)

**US2 (Discovery)**:
- T018-T019 (sequential: discover, filter) → T020-T022 (parallel: mapping, fallback, metadata) → T023-T024 (sequential: CLI, logging)

**US3 (Collection)**:
- T025 (collection function) → T026-T032 (parallel: all field formatting and validation) → T033-T034 (sequential: retry, error handling) → T035-T036 (sequential: CLI, logging)

**US4 (Storage)**:
- T037 (insert method) → T038-T041 (parallel: all constraint/field handling) → T042 (integration) → T043-T044 (sequential: logging, schema creation)

### Parallel Opportunities

**Phase 1 (Setup)**: T003, T004, T005 can run in parallel (different files)

**Phase 2 (Foundational)**: T007, T008, T009 can run in parallel (different files)

**US1**: T011, T012, T013, T014 can run in parallel (different functions in same file or different approaches)

**US2**: T020, T021 can run in parallel (different functions)

**US3**: T026, T027, T028, T029, T030, T031, T032 can run in parallel (independent field transformations)

**US4**: T038, T039, T040, T041 can run in parallel (different aspects of insert method)

**Phase 7**: T045, T046, T047, T050 can run in parallel (different files)

---

## Parallel Example: User Story 3 (Collection)

```bash
# After T025 (collection cycle function) is complete, launch these in parallel:
Task T026: "Convert temperature from 0.01°C to Celsius"
Task T027: "Generate ISO 8601 timestamp with timezone"
Task T028: "Format device_id as hue:{unique_id}"
Task T029: "Set device_type to hue_sensor"
Task T030: "Validate temperature range and flag anomalies"
Task T031: "Extract battery_level from sensor config"
Task T032: "Map signal_strength from reachable boolean"

# All of these are independent transformations that can be implemented simultaneously
```

---

## Implementation Strategy

### MVP First (All P1 Stories)

This feature requires all P1 user stories (US1, US3, US4) to deliver value. US2 (P2) is also essential for the pipeline to work, so treat it as part of MVP:

1. Complete Phase 1: Setup → Project structure ready
2. Complete Phase 2: Foundational → Database schema and validation ready
3. Complete Phase 3: User Story 1 (Authentication) → Can connect to Bridge
4. Complete Phase 4: User Story 2 (Discovery) → Can find sensors
5. Complete Phase 5: User Story 3 (Collection) → Can read temperatures
6. Complete Phase 6: User Story 4 (Storage) → Can persist data
7. **STOP and VALIDATE**: Test complete end-to-end pipeline
8. Complete Phase 7: Polish → Production ready

### Incremental Delivery

1. **Foundation** (Phase 1 + 2) → Database and config ready
2. **Authentication** (Phase 3) → Test: Can authenticate and store credentials
3. **Discovery** (Phase 4) → Test: Can list all sensors with locations
4. **Collection** (Phase 5) → Test: Can retrieve temperature readings (not stored yet)
5. **Storage** (Phase 6) → Test: Complete pipeline stores data in database
6. **Polish** (Phase 7) → Test: Follow quickstart.md end-to-end

### Sequential Execution (Recommended for Solo Developer)

Follow phases 1 → 2 → 3 → 4 → 5 → 6 → 7 in order. Within each phase, implement tasks with [P] markers in parallel or batch them together.

---

## Notes

- [P] tasks = different files or independent functions, no sequential dependencies
- [Story] label (US1, US2, US3, US4) maps task to specific user story for traceability
- Each user story should be independently testable via CLI options
- Constitution principle: "Quick and dirty" - prioritize working solution over perfect code
- Manual verification acceptable - no automated test framework required per constitution
- Commit after each logical task or group of parallel tasks
- Use quickstart.md as acceptance test checklist

---

## Task Count Summary

- **Total Tasks**: 50
- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 4 tasks
- **Phase 3 (US1 - Authentication)**: 8 tasks
- **Phase 4 (US2 - Discovery)**: 7 tasks
- **Phase 5 (US3 - Collection)**: 12 tasks
- **Phase 6 (US4 - Storage)**: 8 tasks
- **Phase 7 (Polish)**: 6 tasks
- **Parallel Opportunities**: 20+ tasks marked [P]

---

## Success Criteria Mapping

Tasks map to success criteria from spec.md:

- **SC-001** (Authenticate within 2 minutes): T010-T017
- **SC-002** (Discover 100% of sensors): T018-T024
- **SC-003** (Collect in <10 seconds): T025-T036
- **SC-004** (100% complete data storage): T037-T044
- **SC-005** (90%+ collection success rate): T033-T034 (error handling)
- **SC-006** (Query performance <1 second): T006 (indexes)
