---
description: "Task list for Sprint 005: Production-Ready System Reliability"
---

# Tasks: Production-Ready System Reliability

**Sprint**: 005-system-reliability  
**Input**: Design documents from `/specs/005-system-reliability/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md (not required), data-model.md (pending), contracts/ (not applicable)

**Tests**: This sprint follows Test-Driven Development (TDD). All tests MUST be written FIRST and FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This project uses:
- `source/` for implementation code
- `tests/` for test files
- `config/` for configuration files
- `data/` for runtime data and alert files

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and sprint-specific structure

- [ ] T001 Create data-model.md documenting health report, retry event, performance metrics, log rotation status, OAuth alert, device registry, and device naming entities
- [ ] T002 Create quickstart.md with health check usage, monitoring alert files, performance baseline guidance, and device naming CLI commands
- [ ] T003 [P] Create checklists/requirements-checklist.md for sprint validation
- [ ] T004 [P] Create checklists/implementation-checklist.md for TDD workflow tracking
- [ ] T005 [P] Create checklists/testing-checklist.md for coverage validation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Retry Logic Foundation (US1, US2 dependency)

**Test First - Write tests BEFORE implementation**:

- [ ] T006 [P] Create tests/test_retry_logic.py with test_retry_success_first_attempt
- [ ] T007 [P] Create test_retry_success_after_transient_failure in tests/test_retry_logic.py
- [ ] T008 [P] Create test_retry_exponential_backoff_timing in tests/test_retry_logic.py
- [ ] T009 [P] Create test_retry_exhaustion_after_max_attempts in tests/test_retry_logic.py
- [ ] T010 [P] Create test_retry_permanent_error_no_retry in tests/test_retry_logic.py
- [ ] T011 [P] Create test_retry_rate_limit_backoff in tests/test_retry_logic.py
- [ ] T012 [P] Create test_retry_logging_events in tests/test_retry_logic.py
- [ ] T013 [P] Create test_retry_concurrent_operations in tests/test_retry_logic.py

**Implementation - Tests must FAIL first**:

- [ ] T014 Create source/utils/retry.py with @retry_with_backoff decorator supporting max attempts, base delay, backoff multiplier, transient vs permanent error classification, comprehensive logging, and thread-safe operation

**Verification**:

- [ ] T015 Run pytest tests/test_retry_logic.py and verify all 8 tests pass with 80%+ coverage

### Performance Measurement Foundation (US5 dependency)

**Test First**:

- [ ] T016 [P] Create tests/test_performance.py with test_measure_collection_cycle_duration
- [ ] T017 [P] Create test_measure_network_payload_size in tests/test_performance.py
- [ ] T018 [P] Create test_baseline_capture_and_comparison in tests/test_performance.py
- [ ] T019 [P] Create test_performance_metrics_logging in tests/test_performance.py
- [ ] T020 [P] Create test_concurrent_measurement_isolation in tests/test_performance.py

**Implementation**:

- [ ] T021 Create source/utils/performance.py with context manager for timing, network payload capture, baseline storage/comparison, metrics logging, and concurrent measurement isolation

**Verification**:

- [ ] T022 Run pytest tests/test_performance.py and verify all 5 tests pass with 80%+ coverage

### Health Check Framework Foundation (US4 dependency)

**Test First**:

- [ ] T023 [P] Create tests/test_health_check.py with test_health_check_all_pass
- [ ] T024 [P] Create test_health_check_partial_failure in tests/test_health_check.py
- [ ] T025 [P] Create test_health_check_critical_failure in tests/test_health_check.py
- [ ] T026 [P] Create test_health_check_timeout in tests/test_health_check.py
- [ ] T027 [P] Create test_health_check_security_no_credential_leak in tests/test_health_check.py
- [ ] T028 [P] Create test_health_check_exit_codes in tests/test_health_check.py
- [ ] T029 [P] Create test_health_check_component_isolation in tests/test_health_check.py

**Implementation**:

- [ ] T030 Create source/health_check.py with individual component validator framework, status aggregation, exit code management (0/1/2), credential security, and 15-second timeout enforcement

**Verification**:

- [ ] T031 Run pytest tests/test_health_check.py and verify all 7 tests pass with 80%+ coverage

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Verified Database Resilience in Production (Priority: P1) 🎯 MVP

**Goal**: Verify WAL mode implementation, test concurrent database operations, validate retry logic under production load scenarios

**Independent Test**: Run concurrent Hue + Amazon AQM collectors for 24 hours, verify zero data loss and no database locked errors

### Tests for User Story 1

**Test First - WAL Mode Verification**:

- [ ] T032 [P] [US1] Create tests/test_database_wal.py with test_wal_mode_enabled_on_init
- [ ] T033 [P] [US1] Create test_wal_checkpoint_interval_configured in tests/test_database_wal.py
- [ ] T034 [P] [US1] Create test_wal_file_growth_bounded in tests/test_database_wal.py
- [ ] T035 [P] [US1] Create test_concurrent_reads_during_write in tests/test_database_wal.py
- [ ] T036 [P] [US1] Create test_concurrent_writes_no_lock_errors in tests/test_database_wal.py

**Test First - Database Retry Integration**:

- [ ] T037 [P] [US1] Create tests/test_database_retry.py with test_database_write_retry_on_lock
- [ ] T038 [P] [US1] Create test_database_retry_exhaustion in tests/test_database_retry.py
- [ ] T039 [P] [US1] Create test_concurrent_collector_writes in tests/test_database_retry.py
- [ ] T040 [P] [US1] Create test_retry_event_logging in tests/test_database_retry.py
- [ ] T041 [US1] Create test_24_hour_continuous_operation in tests/test_database_retry.py (long-running integration test)

### Implementation for User Story 1

- [ ] T042 [US1] Enhance source/storage/manager.py with WAL mode verification on init, checkpoint interval configuration, WAL status logging, and graceful fallback if WAL unavailable
- [ ] T043 [US1] Integrate @retry_with_backoff into source/storage/manager.py database write operations with 3 attempts, exponential backoff, retry event logging, and graceful exhaustion handling

**Verification**:

- [ ] T044 [US1] Run pytest tests/test_database_wal.py tests/test_database_retry.py and verify all 10 tests pass with 80%+ coverage for database resilience

**Checkpoint**: At this point, database resilience should be fully verified and production-ready

---

## Phase 4: User Story 2 - Universal Retry Logic Across All Collectors (Priority: P1) 🎯 MVP

**Goal**: Integrate universal retry logic across Hue and Amazon AQM collectors with consistent behavior for network failures, API timeouts, and rate limits

**Independent Test**: Simulate network failures, API timeouts, rate limits for each collector, verify retry behavior matches configuration and logging is comprehensive

### Tests for User Story 2 - Hue Collector Retry

**Test First**:

- [ ] T045 [P] [US2] Create tests/test_hue_collector_retry.py with test_hue_network_timeout_retry
- [ ] T046 [P] [US2] Create test_hue_bridge_unreachable_retry in tests/test_hue_collector_retry.py
- [ ] T047 [P] [US2] Create test_hue_rate_limit_backoff in tests/test_hue_collector_retry.py
- [ ] T048 [P] [US2] Create test_hue_permanent_error_no_retry in tests/test_hue_collector_retry.py
- [ ] T049 [P] [US2] Create test_hue_retry_exhaustion_continues in tests/test_hue_collector_retry.py

### Tests for User Story 2 - Amazon AQM Collector Retry

**Test First**:

- [ ] T050 [P] [US2] Create tests/test_amazon_collector_retry.py with test_amazon_network_timeout_retry
- [ ] T051 [P] [US2] Create test_amazon_transient_auth_error_retry in tests/test_amazon_collector_retry.py
- [ ] T052 [P] [US2] Create test_amazon_permanent_auth_error_alert in tests/test_amazon_collector_retry.py
- [ ] T053 [P] [US2] Create test_amazon_alert_file_creation in tests/test_amazon_collector_retry.py
- [ ] T054 [P] [US2] Create test_amazon_alert_file_cleared_on_success in tests/test_amazon_collector_retry.py
- [ ] T055 [P] [US2] Create test_amazon_optional_email_notification in tests/test_amazon_collector_retry.py
- [ ] T056 [P] [US2] Create test_amazon_rate_limit_backoff in tests/test_amazon_collector_retry.py

### Implementation for User Story 2

- [ ] T057 [US2] Enhance source/collectors/hue_collector.py with @retry_with_backoff on API calls, transient vs permanent error classification, comprehensive retry event logging with endpoint/error details, and continue-to-next-cycle on exhaustion
- [ ] T058 [US2] Enhance source/collectors/amazon_collector.py with @retry_with_backoff on GraphQL calls, transient auth error retry with token refresh, permanent auth error alert file (data/ALERT_TOKEN_REFRESH_NEEDED.txt), optional email notification (graceful degradation), and auto-clear alert on success

**Verification**:

- [ ] T059 [US2] Run pytest tests/test_hue_collector_retry.py tests/test_amazon_collector_retry.py and verify all 12 tests pass with 80%+ coverage for retry integration

**Checkpoint**: At this point, both collectors should have universal retry logic with comprehensive error handling

---

## Phase 5: User Story 3 - Production-Validated Log Rotation (Priority: P2)

**Goal**: Validate log rotation under production scenarios, implement retry logic for file system errors, verify disk usage bounds

**Independent Test**: Generate high-volume logs, trigger rotation under various conditions, verify disk usage never exceeds 60MB and old logs are archived

### Tests for User Story 3

**Test First**:

- [ ] T060 [P] [US3] Create tests/test_log_rotation.py with test_rotation_at_threshold
- [ ] T061 [P] [US3] Create test_rotation_maintains_integrity in tests/test_log_rotation.py
- [ ] T062 [P] [US3] Create test_backup_count_enforced in tests/test_log_rotation.py
- [ ] T063 [P] [US3] Create test_disk_usage_bounded in tests/test_log_rotation.py
- [ ] T064 [P] [US3] Create test_low_disk_space_handling in tests/test_log_rotation.py
- [ ] T065 [P] [US3] Create test_concurrent_logging_during_rotation in tests/test_log_rotation.py
- [ ] T066 [P] [US3] Create test_rotation_file_system_error_retry in tests/test_log_rotation.py
- [ ] T067 [P] [US3] Create test_rotation_retry_exhaustion in tests/test_log_rotation.py

### Implementation for User Story 3

- [ ] T068 [US3] Enhance source/utils/logging.py with rotation threshold verification (10MB), retry logic for file system errors (3 attempts, exponential backoff), disk usage validation (60MB max), low disk space graceful degradation, and rotation failure critical error logging

**Verification**:

- [ ] T069 [US3] Run pytest tests/test_log_rotation.py and verify all 8 tests pass with 80%+ coverage for log rotation reliability

**Checkpoint**: At this point, log rotation should be production-hardened with comprehensive error handling

---

## Phase 6: User Story 4 - Production Health Check Integration (Priority: P2)

**Goal**: Implement comprehensive health check validating all production deployment prerequisites (database, configuration, secrets, API connectivity, log rotation)

**Independent Test**: Run health checks against various failure scenarios, verify accurate diagnostics with remediation guidance and correct exit codes

### Tests for User Story 4 - Component Validators

**Test First**:

- [ ] T070 [P] [US4] Create tests/test_health_validators.py with test_validate_wal_mode
- [ ] T071 [P] [US4] Create test_validate_configuration in tests/test_health_validators.py
- [ ] T072 [P] [US4] Create test_validate_secrets in tests/test_health_validators.py
- [ ] T073 [P] [US4] Create test_validate_database_write in tests/test_health_validators.py
- [ ] T074 [P] [US4] Create test_validate_log_rotation_config in tests/test_health_validators.py
- [ ] T075 [P] [US4] Create test_validate_hue_bridge_connectivity in tests/test_health_validators.py
- [ ] T076 [P] [US4] Create test_validate_amazon_aqm_connectivity in tests/test_health_validators.py
- [ ] T077 [P] [US4] Create test_validator_security_no_credential_leak in tests/test_health_validators.py

### Tests for User Story 4 - Integration & CLI

**Test First**:

- [ ] T078 [P] [US4] Create tests/test_health_check_integration.py with test_health_check_all_pass_exit_0
- [ ] T079 [P] [US4] Create test_health_check_partial_failure_exit_1 in tests/test_health_check_integration.py
- [ ] T080 [P] [US4] Create test_health_check_critical_failure_exit_2 in tests/test_health_check_integration.py
- [ ] T081 [P] [US4] Create test_health_check_timeout_enforcement in tests/test_health_check_integration.py
- [ ] T082 [P] [US4] Create test_health_check_output_format in tests/test_health_check_integration.py
- [ ] T083 [P] [US4] Create test_health_check_remediation_guidance in tests/test_health_check_integration.py

### Implementation for User Story 4

- [ ] T084 [US4] Implement component validators in source/health_check.py for WAL mode, configuration, secrets (no credential leakage), database write (with rollback), log rotation config, Hue Bridge connectivity, and Amazon AQM connectivity
- [ ] T085 [US4] Complete source/health_check.py with result aggregation, output formatting (pass/fail, errors, remediation), 15-second timeout enforcement, exit codes (0/1/2), and CLI entry point

**Verification**:

- [ ] T086 [US4] Run pytest tests/test_health_validators.py tests/test_health_check_integration.py and verify all 14 tests pass with 80%+ coverage

**Checkpoint**: At this point, production health check should be fully functional and operational

---

## Phase 7: User Story 5 - API Optimization Verification (Priority: P3)

**Goal**: Capture baseline performance metrics, implement Hue Bridge API optimization, verify performance improvements meet targets

**Independent Test**: Measure collection cycle duration and network payload before/after optimization, verify 30% duration improvement and 50% payload reduction

### Tests for User Story 5 - Baseline Capture

**Test First**:

- [ ] T087 [P] [US5] Create tests/test_baseline_capture.py with test_capture_collection_cycle_duration
- [ ] T088 [P] [US5] Create test_capture_network_payload_size in tests/test_baseline_capture.py
- [ ] T089 [P] [US5] Create test_baseline_storage_and_retrieval in tests/test_baseline_capture.py
- [ ] T090 [P] [US5] Create test_baseline_comparison_reporting in tests/test_baseline_capture.py

### Tests for User Story 5 - Hue API Optimization

**Test First**:

- [ ] T091 [P] [US5] Create tests/test_hue_optimization.py with test_sensors_only_endpoint
- [ ] T092 [P] [US5] Create test_payload_size_50_percent_reduction in tests/test_hue_optimization.py
- [ ] T093 [P] [US5] Create test_cycle_duration_30_percent_reduction in tests/test_hue_optimization.py
- [ ] T094 [P] [US5] Create test_optimization_fallback_on_error in tests/test_hue_optimization.py
- [ ] T095 [P] [US5] Create test_optimization_under_high_latency in tests/test_hue_optimization.py

### Implementation for User Story 5

- [ ] T096 [US5] Create baseline capture utility in source/utils/performance.py for measuring current production Hue collector cycle duration and network payload, storing baseline, and generating comparison report
- [ ] T097 [US5] Capture baseline metrics by running current Hue collector with performance measurement and storing results in data/performance_baseline.json
- [ ] T098 [US5] Optimize source/collectors/hue_collector.py with sensors-only endpoint call (vs full bridge config), payload size logging, cycle duration logging, fallback to full config on error, and verification of 50%+ payload reduction and 30%+ duration improvement

**Verification**:

- [ ] T099 [US5] Run pytest tests/test_baseline_capture.py tests/test_hue_optimization.py and verify all 9 tests pass with 80%+ coverage
- [ ] T100 [US5] Compare optimized performance against baseline and verify targets met (30% duration improvement, 50% payload reduction)

**Checkpoint**: All user stories should now be independently functional with verified performance optimization

---

## Phase 8: Integration Testing & Validation

**Purpose**: Comprehensive integration tests simulating production scenarios to validate all success criteria

### 24-Hour Continuous Operation Test

- [ ] T101 Run both Hue and Amazon AQM collectors concurrently for 24 hours monitoring for database locked errors, retry behavior, log rotation, data gaps, and resource usage
- [ ] T102 Verify SC-001: 100% of readings stored with zero data loss
- [ ] T103 Verify SC-002: 95%+ retry success rate for transient lock scenarios
- [ ] T104 Verify SC-008: 7-day unattended operation without manual intervention (extended from 24-hour test)

### Failure Mode Simulation Tests

- [ ] T105 [P] Test network disconnection for both collectors and verify retry logic
- [ ] T106 [P] Test API rate limiting and verify backoff behavior
- [ ] T107 [P] Test database lock contention under concurrent writes
- [ ] T108 [P] Test low disk space handling for log rotation
- [ ] T109 [P] Test invalid credentials detection and health check alerts
- [ ] T110 [P] Test OAuth token expiration and alert file creation for Amazon AQM
- [ ] T111 [P] Test log rotation file system errors and retry behavior
- [ ] T112 Verify SC-007: Consistent retry behavior across all collectors with comprehensive logging

### Health Check Validation Suite

- [ ] T113 [P] Test health check against missing config.yaml
- [ ] T114 [P] Test health check against invalid secrets.yaml format
- [ ] T115 [P] Test health check against missing Hue Bridge username
- [ ] T116 [P] Test health check against missing Amazon credentials
- [ ] T117 [P] Test health check against read-only database file
- [ ] T118 [P] Test health check against non-writable log directory
- [ ] T119 [P] Test health check against WAL mode disabled
- [ ] T120 [P] Test health check against unreachable Hue Bridge
- [ ] T121 [P] Test health check against invalid Amazon AQM credentials
- [ ] T122 Test health check against multiple simultaneous failures
- [ ] T123 Verify SC-004: Health check completes in <15 seconds and accurately identifies all 10 failure scenarios

### Performance Validation

- [ ] T124 Verify SC-005: Hue collection cycles 30%+ faster than baseline
- [ ] T125 Verify SC-006: Network transfer 50%+ smaller than baseline
- [ ] T126 Verify SC-003: Log disk usage <60MB after 30-day simulation (accelerated logging test)

---

## Phase 9: User Story 6 - Device Registry with Named Devices and Locations (Priority: P3)

**Goal**: Create a device registry table to store device names and locations, enable setting/amending device names, and automatically populate device location data in readings

**Independent Test**: Can be tested by adding devices to registry, setting custom names, collecting readings, and verifying device names and locations are stored correctly in both registry and readings tables

### Tests for User Story 6 - Device Registry Schema

**Test First**:

- [ ] T127 [P] [US6] Create tests/test_device_registry.py with test_device_registry_table_creation
- [ ] T128 [P] [US6] Create test_device_insert_with_name_and_location in tests/test_device_registry.py
- [ ] T129 [P] [US6] Create test_device_unique_constraint in tests/test_device_registry.py
- [ ] T130 [P] [US6] Create test_device_name_update in tests/test_device_registry.py
- [ ] T131 [P] [US6] Create test_device_location_update in tests/test_device_registry.py

### Tests for User Story 6 - Device Name Management

**Test First**:

- [ ] T132 [P] [US6] Create tests/test_device_naming.py with test_set_device_name_new_device
- [ ] T133 [P] [US6] Create test_set_device_name_existing_device in tests/test_device_naming.py
- [ ] T134 [P] [US6] Create test_amend_device_name_without_history_update in tests/test_device_naming.py
- [ ] T135 [P] [US6] Create test_amend_device_name_with_recursive_history_update in tests/test_device_naming.py
- [ ] T136 [P] [US6] Create test_get_device_name_from_registry in tests/test_device_naming.py
- [ ] T137 [P] [US6] Create test_list_all_devices_with_names in tests/test_device_naming.py

### Tests for User Story 6 - Location Auto-Discovery

**Test First**:

- [ ] T138 [P] [US6] Create tests/test_device_location.py with test_extract_location_from_hue_sensor
- [ ] T139 [P] [US6] Create test_extract_location_from_amazon_aqm_device in tests/test_device_location.py
- [ ] T140 [P] [US6] Create test_store_location_in_device_registry in tests/test_device_location.py
- [ ] T141 [P] [US6] Create test_location_propagation_to_readings in tests/test_device_location.py
- [ ] T142 [P] [US6] Create test_location_override_via_config in tests/test_device_location.py

### Tests for User Story 6 - Integration with Collectors

**Test First**:

- [ ] T143 [P] [US6] Create tests/test_device_registry_integration.py with test_hue_collector_uses_device_registry
- [ ] T144 [P] [US6] Create test_amazon_collector_uses_device_registry in tests/test_device_registry_integration.py
- [ ] T145 [P] [US6] Create test_readings_include_device_name_and_location in tests/test_device_registry_integration.py
- [ ] T146 [P] [US6] Create test_unknown_device_auto_registered in tests/test_device_registry_integration.py

### Implementation for User Story 6

- [ ] T147 [US6] Create device_registry table in source/storage/schema.py with columns: device_id (PK), device_type, device_name, location, unique_id, model_info, first_seen, last_seen, is_active
- [ ] T148 [US6] Add database migration support in source/storage/manager.py to create device_registry table for existing databases
- [ ] T149 [US6] Create source/storage/device_manager.py with functions: register_device(), set_device_name(), amend_device_name(), get_device_name(), list_devices(), update_device_location()
- [ ] T150 [US6] Implement recursive history update in source/storage/device_manager.py for amend_device_name() to optionally update historical readings with new device name
- [ ] T151 [US6] Enhance source/collectors/hue_collector.py to register discovered sensors in device_registry and use device names from registry when storing readings
- [ ] T152 [US6] Enhance source/collectors/amazon_collector.py to register discovered devices in device_registry and use device names from registry when storing readings
- [ ] T153 [US6] Create CLI command in source/storage/device_manager.py for setting device names: python source/storage/device_manager.py --set-name <device_id> <name>
- [ ] T154 [US6] Create CLI command in source/storage/device_manager.py for amending device names: python source/storage/device_manager.py --amend-name <device_id> <name> [--recursive]
- [ ] T155 [US6] Create CLI command in source/storage/device_manager.py for listing devices: python source/storage/device_manager.py --list-devices

**Verification**:

- [ ] T156 [US6] Run pytest tests/test_device_registry.py tests/test_device_naming.py tests/test_device_location.py tests/test_device_registry_integration.py and verify all 21 tests pass with 80%+ coverage
- [ ] T157 [US6] Test device name CLI commands manually: set name for Hue sensor, amend with --recursive, verify readings updated
- [ ] T158 [US6] Run collection cycle and verify device names appear in output: "✅ Utility: 20.29°C [Battery: 100%]" uses device name from registry

**Checkpoint**: At this point, device registry should be fully functional with named devices and automatic location tracking

---

## Phase 10: Integration Testing & Validation

**Purpose**: Comprehensive integration tests simulating production scenarios to validate all success criteria

### 24-Hour Continuous Operation Test

- [ ] T159 Run both Hue and Amazon AQM collectors concurrently for 24 hours monitoring for database locked errors, retry behavior, log rotation, data gaps, and resource usage
- [ ] T160 Verify SC-001: 100% of readings stored with zero data loss
- [ ] T161 Verify SC-002: 95%+ retry success rate for transient lock scenarios
- [ ] T162 Verify SC-008: 7-day unattended operation without manual intervention (extended from 24-hour test)

### Failure Mode Simulation Tests

- [ ] T163 [P] Test network disconnection for both collectors and verify retry logic
- [ ] T164 [P] Test API rate limiting and verify backoff behavior
- [ ] T165 [P] Test database lock contention under concurrent writes
- [ ] T166 [P] Test low disk space handling for log rotation
- [ ] T167 [P] Test invalid credentials detection and health check alerts
- [ ] T168 [P] Test OAuth token expiration and alert file creation for Amazon AQM
- [ ] T169 [P] Test log rotation file system errors and retry behavior
- [ ] T170 Verify SC-007: Consistent retry behavior across all collectors with comprehensive logging

### Health Check Validation Suite

- [ ] T171 [P] Test health check against missing config.yaml
- [ ] T172 [P] Test health check against invalid secrets.yaml format
- [ ] T173 [P] Test health check against missing Hue Bridge username
- [ ] T174 [P] Test health check against missing Amazon credentials
- [ ] T175 [P] Test health check against read-only database file
- [ ] T176 [P] Test health check against non-writable log directory
- [ ] T177 [P] Test health check against WAL mode disabled
- [ ] T178 [P] Test health check against unreachable Hue Bridge
- [ ] T179 [P] Test health check against invalid Amazon AQM credentials
- [ ] T180 Test health check against multiple simultaneous failures
- [ ] T181 Verify SC-004: Health check completes in <15 seconds and accurately identifies all 10 failure scenarios

### Performance Validation

- [ ] T182 Verify SC-005: Hue collection cycles 30%+ faster than baseline
- [ ] T183 Verify SC-006: Network transfer 50%+ smaller than baseline
- [ ] T184 Verify SC-003: Log disk usage <60MB after 30-day simulation (accelerated logging test)

### Device Registry Validation

- [ ] T185 [P] Verify device names persist across collection cycles
- [ ] T186 [P] Verify recursive name updates correctly modify historical readings
- [ ] T187 Verify device registry auto-registration for new devices during collection

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final Definition of Done verification

### Documentation Updates

- [ ] T188 [P] Update plan.md with implementation outcomes and metrics
- [ ] T189 [P] Update README.md with health check and monitoring guidance
- [ ] T190 [P] Create operational runbook in quickstart.md for health check usage, monitoring alert files, and troubleshooting common failures
- [ ] T191 [P] Document performance baseline and optimization results
- [ ] T192 [P] Document device registry usage in README.md with examples for setting/amending device names

### Code Quality & Security

- [ ] T193 Run pytest with coverage report and verify 80%+ coverage for all new code
- [ ] T194 Security review: verify no credential leakage in logs, health check output, or error messages
- [ ] T195 Code cleanup and refactoring for consistency across collectors
- [ ] T196 Update all docstrings and inline comments for reliability features

### Definition of Done Verification

- [ ] T197 Verify all unit tests pass in Python venv: pytest tests/
- [ ] T198 Verify TDD approach followed (all tests written before implementation)
- [ ] T199 Verify 80%+ test coverage for all new code (retry logic, health check, performance utils, collector enhancements, log rotation, device registry)
- [ ] T200 Verify all code committed to git with descriptive messages referencing sprint 005
- [ ] T201 Verify data collection working in real environment (24-hour + 7-day tests completed)
- [ ] T202 Verify no breaking changes to existing data format or API contracts
- [ ] T203 Verify all documentation complete (spec.md ✅, plan.md ✅, quickstart.md, README, data-model.md)
- [ ] T204 Run quickstart.md validation scenarios and verify all pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - US1 (Database Resilience): Can start after Foundational
  - US2 (Retry Integration): Can start after Foundational
  - US3 (Log Rotation): Can start after Foundational
  - US4 (Health Check): Can start after Foundational (will integrate US1 results)
  - US5 (API Optimization): Can start after Foundational
  - US6 (Device Registry): Can start after Foundational (will integrate with collectors from US2)
- **Integration Testing (Phase 10)**: Depends on US1, US2, US3, US4, US5, US6 completion
- **Polish (Phase 11)**: Depends on Integration Testing completion

### User Story Dependencies

- **US1 (Database Resilience - P1)**: Independent - requires only Foundational phase
- **US2 (Retry Integration - P1)**: Independent - requires only Foundational phase
- **US3 (Log Rotation - P2)**: Independent - requires only Foundational phase
- **US4 (Health Check - P2)**: Integrates with US1 (WAL validation) but independently testable
- **US5 (API Optimization - P3)**: Independent - requires only Foundational phase
- **US6 (Device Registry - P3)**: Integrates with collectors (US2) but independently testable - requires database schema migration support

### Within Each User Story

1. **Tests FIRST** (must FAIL before implementation):
   - Write all test files for the story
   - Run tests and verify they fail (no implementation yet)
2. **Implementation**:
   - Implement functionality to make tests pass
   - Run tests repeatedly until all pass
3. **Verification**:
   - Confirm 80%+ coverage for the story
   - Story complete and independently testable

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003, T004, T005 can run in parallel

**Phase 2 (Foundational) - Within each subsection**:
- T006-T013 (retry tests) can run in parallel
- T016-T020 (performance tests) can run in parallel
- T023-T029 (health check tests) can run in parallel

**Phase 3 (US1)**:
- T032-T036 (WAL tests) can run in parallel
- T037-T040 (retry tests) can run in parallel

**Phase 4 (US2)**:
- T045-T049 (Hue retry tests) can run in parallel
- T050-T056 (Amazon retry tests) can run in parallel

**Phase 5 (US3)**:
- T060-T067 (log rotation tests) can run in parallel

**Phase 6 (US4)**:
- T070-T077 (validator tests) can run in parallel
- T078-T083 (integration tests) can run in parallel

**Phase 7 (US5)**:
- T087-T090 (baseline tests) can run in parallel
- T091-T095 (optimization tests) can run in parallel

**Phase 9 (US6)**:
- T127-T131 (device registry schema tests) can run in parallel
- T132-T137 (device naming tests) can run in parallel
- T138-T142 (location discovery tests) can run in parallel
- T143-T146 (integration tests) can run in parallel

**Phase 10 (Integration)**:
- T163-T169 (failure mode tests) can run in parallel
- T171-T179 (health check scenarios) can run in parallel
- T185-T186 (device registry validation) can run in parallel

**Phase 11 (Polish)**:
- T188-T192 (documentation) can run in parallel

**Entire User Stories** (after Foundational complete):
- US1, US2, US3, US5, US6 can be worked on in parallel (different team members)
- US4 can start in parallel but will integrate US1 WAL validation results

---

## Parallel Example: Foundational Phase - Retry Logic

```bash
# Launch all retry logic tests together (T006-T013):
- Create test_retry_success_first_attempt
- Create test_retry_success_after_transient_failure
- Create test_retry_exponential_backoff_timing
- Create test_retry_exhaustion_after_max_attempts
- Create test_retry_permanent_error_no_retry
- Create test_retry_rate_limit_backoff
- Create test_retry_logging_events
- Create test_retry_concurrent_operations

# Then implement source/utils/retry.py to make all tests pass
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only - Both P1)

1. **Complete Phase 1**: Setup (documentation structure)
2. **Complete Phase 2**: Foundational (CRITICAL - retry logic, performance utils, health check framework)
3. **Complete Phase 3**: User Story 1 (Database Resilience)
4. **Complete Phase 4**: User Story 2 (Universal Retry Logic)
5. **STOP and VALIDATE**: Run 24-hour integration test with both collectors
6. **Result**: Production-ready system with verified database resilience and universal retry logic

This MVP delivers the highest-priority reliability features (P1 stories) and enables production deployment with confidence.

### Incremental Delivery

1. **Foundation** (Phase 1-2) → Core utilities ready
2. **MVP** (Phase 3-4: US1 + US2) → Test 24 hours → **Deploy to production**
3. **Enhanced** (Phase 5: US3) → Add log rotation validation → Test → Deploy update
4. **Monitored** (Phase 6: US4) → Add health check → Test → Deploy update
5. **Optimized** (Phase 7: US5) → Add performance optimization → Test → Deploy update
6. **Named Devices** (Phase 9: US6) → Add device registry → Test → Deploy update

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With 2-3 developers (after Foundational phase complete):

**Option 1: MVP Priority**
- Developer A: US1 (Database Resilience)
- Developer B: US2 (Universal Retry Logic)
- Once US1 + US2 complete: 24-hour integration test → Production deployment
- Then proceed to US3, US4, US5, US6 in priority order

**Option 2: Full Parallel**
- Developer A: US1 + US4 (Database + Health Check integration)
- Developer B: US2 + US6 (Universal Retry + Device Registry)
- Developer C: US3 + US5 (Log Rotation + Optimization)
- All stories integrate at Phase 10

---

## Task Count Summary

- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 26 tasks (8 retry tests + 1 impl + 1 verify + 5 perf tests + 1 impl + 1 verify + 7 health tests + 1 impl + 1 verify)
- **Phase 3 (US1)**: 13 tasks (10 tests + 2 impl + 1 verify)
- **Phase 4 (US2)**: 15 tasks (12 tests + 2 impl + 1 verify)
- **Phase 5 (US3)**: 10 tasks (8 tests + 1 impl + 1 verify)
- **Phase 6 (US4)**: 17 tasks (14 tests + 2 impl + 1 verify)
- **Phase 7 (US5)**: 14 tasks (9 tests + 3 impl + 2 verify)
- **Phase 8 (Integration)**: 26 tasks (legacy - see Phase 10)
- **Phase 9 (US6)**: 32 tasks (21 tests + 9 impl + 3 verify)
- **Phase 10 (Integration)**: 29 tasks (24-hour test + failure modes + health check + performance + device registry validation)
- **Phase 11 (Polish)**: 17 tasks (documentation + code quality + definition of done)

**Total**: 204 tasks

**Test Coverage Focus**: 80%+ coverage target (not specific test count requirement)

---

## Notes

- **[P] tasks** = different files, no dependencies - can run in parallel
- **[Story] label** maps task to specific user story for traceability
- **TDD Critical**: ALL tests must be written FIRST and FAIL before implementation
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Foundational phase is BLOCKING**: No user story work until T031 complete

---

**Generated**: 20 November 2025  
**Sprint**: 005-system-reliability  
**Constitutional Compliance**: ✅ Verified (TDD, 80% coverage, independent user stories)
