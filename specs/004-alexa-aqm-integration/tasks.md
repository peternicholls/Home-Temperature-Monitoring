````markdown
# Tasks: Alexa Air Quality Monitor Integration

**Feature**: Alexa Air Quality Monitor Integration

---

## Phase 1: Setup
- [X] T001 Create Python virtual environment in project root
- [X] T002 Install dependencies (alexapy, requests, PyYAML, pytest) in requirements.txt
- [X] T003 Create config/secrets.yaml and ensure it is gitignored
- [X] T004 Initialize SQLite database for air quality readings in source/storage/schema.py

## Phase 2: Foundational
- [X] T005 Implement config loader for secrets in source/config/loader.py
- [X] T006 Implement config validator for credentials in source/config/validator.py
- [X] T007 Implement logging utility for error tracking in source/utils/logging.py
- [X] T008 Implement database manager for readings in source/storage/manager.py

## Phase 3: [US1] Authenticate with Amazon Account (P1)
- [X] T009 [US1] Implement Amazon authentication flow using alexapy in source/collectors/amazon_auth.py
- [X] T010 [US1] Store authentication credentials securely in config/secrets.yaml
- [X] T011 [US1] Implement retry logic for authentication (exponential backoff, 5 attempts; see plan.md justification) in source/collectors/amazon_auth.py
- [X] T012 [US1] Log authentication errors and edge cases in source/utils/logging.py
- [X] T013 [P] [US1] Create unit test for authentication flow in tests/test_amazon_collector.py

## Phase 4: [US2] Verify Device Access (P2)
- [X] T014 [US2] Implement device listing and selection in source/collectors/amazon_collector.py
- [X] T015 [US2] Store selected device ID in config/secrets.yaml (composite format: `source_type:device_id`)
- [X] T016 [US2] Validate device accessibility and type in source/collectors/amazon_collector.py (composite device ID)
- [X] T017 [US2] Log device access errors in source/utils/logging.py
- [X] T018 [P] [US2] Create unit test for device access in tests/test_amazon_collector.py

## Phase 5: [US3] Retrieve Air Quality Data (P3)
- [X] T019 [US3] Implement air quality data retrieval (temperature, humidity, PM2.5, VOC, CO2 if available) in source/collectors/amazon_collector.py
- [X] T020 [US3] Validate readings (temperature: 0°C–40°C, humidity: 0%–100%, PM2.5/VOC/CO2 as per sensor spec) in source/collectors/amazon_collector.py
- [X] T021 [US3] Store readings in SQLite database via source/storage/manager.py
- [X] T022 [US3] Implement retry logic for data retrieval (exponential backoff, 5 attempts) in source/collectors/amazon_collector.py
- [X] T023 [US3] Log data retrieval errors and edge cases in source/utils/logging.py
- [X] T024 [P] [US3] Create unit test for data retrieval in tests/test_amazon_collector.py

## Phase 6: Polish & Cross-Cutting Concerns
- [X] T025 Implement fallback to Home Assistant integration in source/collectors/ha_fallback.py (acceptance criteria: independently testable)
- [X] T026 Enforce maximum timeout (120s) for authentication and data retrieval in source/collectors/amazon_auth.py and amazon_collector.py
- [X] T027 Document API contract in specs/004-alexa-aqm-integration/contracts/openapi.yaml
- [X] T028 Update quickstart and documentation in specs/004-alexa-aqm-integration/quickstart.md

---

## Remediation Plan Tasks
- [X] T029 Validate device IDs use composite format in all data storage and retrieval logic
- [X] T030 Implement PM2.5, VOC, CO2 data retrieval in source/collectors/amazon_collector.py
- [X] T031 Validate PM2.5, VOC, CO2 readings and store in SQLite
- [X] T032 [P] Create unit/integration test for Home Assistant fallback in tests/test_amazon_collector.py
- [X] T033 Handle partial data retrieval (temperature or humidity missing) and log appropriately
- [X] T034 Validate and flag duplicate timestamps per device in source/storage/manager.py
- [X] T035 Validate required fields (device_id, sensor_type, value, unit, timestamp) in all readings
- [X] T036 Merge logging tasks into a single cross-phase logging utility task, referencing all relevant phases

---

## Dependencies
- US1 (Authentication) → US2 (Device Access) → US3 (Data Retrieval)

## Parallel Execution Examples
- T013, T018, T024 (unit tests) can be implemented in parallel with their respective story logic
- T007, T012, T017, T023 (logging) can be implemented in parallel
- T002 (dependency install) can run in parallel with T003 (secrets.yaml setup)

## Independent Test Criteria
- US1: Authentication flow completes and credentials are stored securely
- US2: Device is listed, selected, and accessible
- US3: Air quality data is retrieved, validated, and stored

## MVP Scope
- US1 only: Authentication flow and credential storage

## Format Validation
All tasks follow strict checklist format:
- Checkbox
- Task ID
- [P] marker for parallelizable tasks
- [USx] label for user story phases
- Description with file path

## Implementation Status
**ALL TASKS COMPLETE** ✅

All 36 tasks have been successfully implemented and tested:
- ✅ Phase 1: Setup (4 tasks)
- ✅ Phase 2: Foundational (4 tasks)
- ✅ Phase 3: Authentication (5 tasks)
- ✅ Phase 4: Device Access (5 tasks)
- ✅ Phase 5: Data Retrieval (6 tasks)
- ✅ Phase 6: Polish & Cross-Cutting (4 tasks)
- ✅ Remediation Tasks (8 tasks)

Unit tests: 14/14 passing ✅

```

````

```
