---
description: "Task list for Amazon Alexa Air Quality Monitor Integration - Sprint 3"
---

# Tasks: Amazon Alexa Air Quality Monitor Integration - Sprint 3 (Database Integration)

**Feature**: Amazon Alexa Air Quality Monitor Integration
**Sprint**: 3 - Database Integration
**Status**: Sprint 2 Research Complete ✅ - Ready for Integration
**Estimated Duration**: 115 minutes (~2 hours)

**Prerequisites**: 
- Sprint 2 research complete (16 iterations, working API discovered)
- Working collector code in source/collectors/amazon_collector.py
- Web UI cookie capture working at http://localhost:5001/setup
- Integration plan in docs/Amazon-Alexa-Air-Quality-Monitoring/amazon-aqm-integration-plan.md

**Organization**: Tasks organized by integration phase based on amazon-aqm-integration-plan.md

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- File paths use existing project structure: `source/`, `config/`, `tests/`

---

## Phase 1: Setup (Database Schema Updates)

**Purpose**: Update database schema to support new AQM sensor fields (co_ppm, iaq_score)

**Estimated Time**: 5 minutes

- [X] T001 Add `co_ppm REAL CHECK(co_ppm IS NULL OR co_ppm >= 0)` column to schema in source/storage/schema.py
- [X] T002 Add `iaq_score REAL CHECK(iaq_score IS NULL OR (iaq_score >= 0 AND iaq_score <= 100))` column to schema in source/storage/schema.py
- [X] T003 Update required_cols list in source/storage/manager.py to include co_ppm and iaq_score
- [X] T004 Add migration logic in source/storage/manager.py for existing databases to add new columns
- [X] T005 Test schema migration on copy of production database and verify columns added

**Checkpoint**: ✅ Database schema ready for AQM data storage with new sensor fields

---

## Phase 2: Foundational (Configuration & Web UI Documentation)

**Purpose**: Core configuration setup and web UI documentation required by all user stories

**Estimated Time**: 25 minutes

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Add amazon_aqm section to config/config.yaml with enabled, domain, device_serial, timeout_seconds, collection_interval
- [X] T007 [P] Configure device_locations mapping in config/config.yaml (e.g., "GAJ23005314600H3": "Living Room")
- [X] T008 [P] Set retry_attempts (3), retry_backoff_base (1.0), max_timeout (120) in config/config.yaml amazon_aqm section
- [X] T009 [P] Add sensor collection toggles to config/config.yaml (collect_temperature, collect_humidity, collect_pm25, collect_voc, collect_co, collect_iaq)
- [X] T010 Verify config/secrets.yaml has amazon_aqm.cookies structure with session-id, session-token, csrf placeholders
- [X] T011 Add run_amazon_login() function to source/collectors/amazon_auth.py for web UI integration
- [X] T012 Test web UI cookie capture at http://localhost:5001/setup and verify cookies saved

**Checkpoint**: ✅ Configuration complete, web UI working - user stories can now proceed

---

## Phase 3: User Story 1 - Authenticate with Amazon Account (Priority: P1) 🎯 MVP

**Goal**: Enable users to authenticate with Amazon account via web UI to access AQM data

**Independent Test**: User can navigate to http://localhost:5001/setup, complete login, and see confirmation with cookie count

**Why P1**: Without authentication, system cannot access any device data - foundation for all functionality

### Implementation for User Story 1

- [X] T013 [US1] Update source/web/templates/setup.html with clear Amazon login instructions and button styling
- [X] T014 [US1] Add validate_amazon_cookies() function in source/collectors/amazon_auth.py to check cookie structure
- [X] T015 [US1] Implement check_cookie_expiration() in source/collectors/amazon_auth.py for 24-hour window validation
- [X] T016 [US1] Add clear error messages for authentication failures in source/collectors/amazon_auth.py (missing cookies, expired, invalid)
- [X] T017 [US1] Add logging for authentication attempts, successes, and failures in source/collectors/amazon_auth.py
- [X] T018 [US1] Test authentication flow end-to-end with real Amazon account and verify cookies stored
- [X] T019 [US1] Verify cookie structure contains all 18 required cookies in config/secrets.yaml

**Checkpoint**: ✅ User Story 1 complete - users can authenticate and cookies are stored securely

---

## Phase 4: User Story 2 - Verify Device Access (Priority: P2)

**Goal**: Confirm AQM device is accessible and linked to authenticated account

**Independent Test**: Can list devices via GraphQL and see correct entity ID and serial number

**Why P2**: Device must be accessible before data retrieval; early verification prevents later issues

### Implementation for User Story 2

- [X] T020 [US2] Verify source/collectors/amazon_collector.py list_devices() uses correct GraphQL endpoint and query
- [X] T021 [US2] Implement device type filtering for Air Quality Monitor in source/collectors/amazon_collector.py list_devices()
- [X] T022 [US2] Add device accessibility status check in source/collectors/amazon_collector.py (check if entity_id is valid)
- [X] T023 [US2] Implement device selection logic in source/collectors/amazon_collector.py (from config device_serial or auto-discover first device)
- [X] T024 [US2] Add logging for device discovery results (count, names, serials) in source/collectors/amazon_collector.py
- [X] T025 [US2] Create CLI --discover mode in source/collectors/amazon_collector.py to list all devices with status
- [X] T026 [US2] Test device discovery with physical AQM device and verify entity ID and serial extracted
- [X] T027 [US2] Verify device entity ID format (UUID) and serial number format (GAJ...)

**Checkpoint**: ✅ User Story 2 complete - device accessible and properly identified

---

## Phase 5: User Story 3 - Retrieve Air Quality Data (Priority: P3)

**Goal**: Successfully retrieve all sensor readings from AQM and store in database

**Independent Test**: Can collect readings, validate all 8 sensors, and verify database storage

**Why P3**: Validates end-to-end integration and enables core monitoring functionality

### Implementation for User Story 3

- [X] T028 [P] [US3] Add format_reading_for_db() method in source/collectors/amazon_collector.py to format readings for database insertion
- [X] T029 [P] [US3] Implement location mapping from config device_locations in format_reading_for_db() method
- [X] T030 [US3] Add collect_and_store() convenience function in source/collectors/amazon_collector.py wrapping collection and storage
- [X] T031 [US3] Implement device_id formatting as alexa:serial in format_reading_for_db() method
- [X] T032 [US3] Add raw_response storage option (configurable via collect_raw_response) in format_reading_for_db()
- [X] T033 [US3] Create source/collectors/amazon_aqm_collector_main.py main collection script with argparse
- [X] T034 [US3] Implement --collect-once mode in amazon_aqm_collector_main.py for single collection run
- [X] T035 [US3] Implement --continuous mode in amazon_aqm_collector_main.py with collection_interval from config
- [X] T036 [US3] Add exponential backoff retry logic in amazon_aqm_collector_main.py (1s, 2s, 4s - up to 3 attempts)
- [X] T037 [US3] Implement graceful error handling for API failures in amazon_aqm_collector_main.py (network errors, auth failures, device offline)
- [X] T038 [US3] Add logging for collection cycles, successes, failures in amazon_aqm_collector_main.py
- [X] T039 [US3] Test single collection with --collect-once flag and verify readings stored
- [X] T040 [US3] Verify all 8 sensor readings stored correctly in database (temperature_celsius, humidity_percent, pm25_ugm3, voc_ppb, co_ppm, iaq_score, unknown_7, connectivity)
- [X] T041 [US3] Test validation rejects out-of-range values (temp > 40°C, humidity > 100%, negative values)
- [X] T042 [US3] Test duplicate timestamp detection works (UNIQUE constraint on device_id, timestamp)
- [X] T043 [US3] Test continuous collection for 15 minutes (3 cycles at 5-min intervals) and verify stability

**Checkpoint**: ✅ User Story 3 complete - full data collection and storage working

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, testing, and final validation

**Estimated Time**: 15 minutes

- [X] T044 [P] Update README.md with AQM integration section, features, and installation instructions
- [X] T045 [P] Document cookie capture process in README.md with step-by-step web UI instructions
- [X] T046 [P] Update specs/004-alexa-aqm-integration/quickstart.md with database integration examples (format_reading_for_db, collect_and_store)
- [X] T047 [P] Add troubleshooting section to README.md for common errors (cookie expiration, device offline, API failures, rate limiting)
- [X] T048 Update CHANGELOG.md with Sprint 3 database integration completion and new features
- [X] T049 [P] Add inline code comments to new functions in amazon_collector.py (format_reading_for_db, collect_and_store)
- [X] T050 Run quickstart.md validation to verify all code examples work end-to-end
- [X] T051 Test error scenarios (expired cookies, offline device, network failure, invalid sensor data, database locked)
- [X] T052 [P] Add Makefile targets for AQM operations (aqm-discover, aqm-collect-once, aqm-continuous, aqm-test)

**Checkpoint**: ✅ All 52 tasks complete - Sprint 3 Amazon AQM database integration ready for production

**Checkpoint**: ✅ All documentation complete, validated, and production-ready

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - US1 (Authentication): Can start after Foundational
  - US2 (Device Access): Logically after US1 (needs auth cookies)
  - US3 (Data Retrieval): Requires US1 + US2 (needs auth + device)
- **Polish (Phase 6)**: Depends on all user stories being complete

### Sequential Execution Order (Recommended for Solo Developer)

1. **Phase 1: Setup** (T001-T005) → ~5 min
2. **Phase 2: Foundational** (T006-T012) → ~25 min
3. **Phase 3: US1 Authentication** (T013-T019) → ~15 min
4. **Phase 4: US2 Device Access** (T020-T027) → ~15 min
5. **Phase 5: US3 Data Retrieval** (T028-T043) → ~40 min
6. **Phase 6: Polish** (T044-T052) → ~15 min

**Total Estimated Time**: ~115 minutes (matches integration plan)

### Parallel Opportunities Within Phases

**Phase 2 (Foundational)**:
- T006, T007, T008, T009 can run in parallel (different config sections)
- T011 can run in parallel with config tasks

**Phase 5 (US3)**:
- T028, T029 can run in parallel (different functions in same file)

**Phase 6 (Polish)**:
- T044, T045, T046, T047, T049, T052 can all run in parallel (different files)

---

## Testing Strategy

### Per User Story Testing

**User Story 1 (Authentication)**:
- ✅ Web UI loads at http://localhost:5001/setup
- ✅ Browser automation opens and captures cookies
- ✅ Cookies saved to secrets.yaml with correct structure (18 cookies)
- ✅ Cookie validation detects expired cookies
- ✅ Error messages clear and actionable

**User Story 2 (Device Access)**:
- ✅ --discover mode lists devices correctly
- ✅ Device filtering shows only AQM devices
- ✅ Device serial and entity ID extracted correctly
- ✅ Accessibility status check works
- ✅ Device selection logic (config vs auto-discover) works

**User Story 3 (Data Retrieval)**:
- ✅ --collect-once retrieves all 8 sensors
- ✅ Database insertion uses new schema columns (co_ppm, iaq_score)
- ✅ Validation rejects invalid data
- ✅ Duplicate detection works (UNIQUE constraint)
- ✅ Retry logic handles failures gracefully
- ✅ Continuous collection stable over 15+ minutes

### Integration Testing (After All Phases)

- Full flow: authenticate → discover → collect → store
- Cookie expiration scenario
- Device offline scenario
- Network failure scenario
- Database recovery from locked state
- Rate limiting handling

---

## Success Criteria

| Story | Criteria | Validation Method |
|-------|----------|-------------------|
| US1 | Cookie capture within 2 minutes | Time from button click to confirmation |
| US1 | 18 cookies saved to secrets.yaml | Check file content |
| US1 | Clear error messages on failure | Review error message quality |
| US2 | Device listed within 10 seconds | Time discovery request |
| US2 | Correct entity ID and serial extracted | Verify UUID and GAJ... format |
| US2 | Device selection works | Test config and auto-discover paths |
| US3 | All 8 sensors stored in database | Query database for latest reading |
| US3 | Validation catches invalid data | Test with out-of-range values |
| US3 | Duplicate detection works | Attempt to store same timestamp twice |
| US3 | Continuous collection stable | Run for 15+ minutes without errors |
| All | Feedback within 10 seconds | Progress updates during operations |
| All | Final result within 120 seconds | Maximum timeout enforcement |

---

## Implementation Notes

### From Sprint 2 Research

- ✅ Working API endpoint: POST https://alexa.amazon.co.uk/api/phoenix/state
- ✅ Critical detail: `entityType: "ENTITY"` (not "APPLIANCE")
- ✅ Data parsing: capabilityStates are JSON strings requiring parsing
- ✅ Instance mapping: Instance IDs map to sensor types (4=humidity, 5=VOC, 6=PM2.5, 8=CO, 9=IAQ)
- ✅ Web UI already implemented in source/web/app.py
- ✅ Cookie capture working via Playwright

### Integration Pattern

Follow existing Hue collector pattern:
- Similar structure to source/collectors/hue_collector.py
- Configuration in config/config.yaml amazon_aqm section
- Secrets in config/secrets.yaml amazon_aqm.cookies
- Main script with --discover, --collect-once, --continuous modes
- Database storage via source/storage/manager.py

### Known Limitations

1. **Cookie Expiration**: ~24 hours - requires periodic re-authentication
2. **Unknown Sensor**: Instance 7 purpose not identified (stored for analysis)
3. **Single Region**: Tested with UK domain only (configurable)
4. **Manual Location**: Device locations must be manually mapped in config

---

## Risk Mitigation

| Risk | Mitigation Tasks | Status |
|------|------------------|--------|
| Cookie Expiration | T014, T015, T016 - validation and error handling | Planned |
| API Rate Limiting | T036 - exponential backoff, config interval | Planned |
| Schema Migration | T004, T005 - migration logic and testing | Planned |
| Data Quality | T040, T041 - validation and range checks | Planned |

---

**Total Tasks**: 52
**Completed**: 0 (Sprint 3 starting)
**Estimated Duration**: 115 minutes (~2 hours)
**Parallel Opportunities**: 15+ tasks
**Sprint 2 Status**: ✅ Research complete (16 iterations, working solution found)
**Sprint 3 Status**: 🚀 Ready to begin database integration

---

**Ready for Sprint 3 execution** - All prerequisites from Sprint 2 research complete.

````

```
