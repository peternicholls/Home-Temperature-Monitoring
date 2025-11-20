# Remediation Plan: Alexa Air Quality Monitor Integration

**Date:** 20 November 2025
**Scope:** All identified issues from specification analysis

---

## CRITICAL Issues

### 1. Retry Policy (5 vs 3 attempts)
- Add explicit justification for 5 attempts (Amazon API/network reliability) in plan.md “Complexity Tracking” and “Constitution Check” tables.
- In tasks.md, add a note to the retry logic tasks referencing this justification and constitution alignment.

### 2. Device ID Format
- Ensure all references to device IDs specify composite format (`source_type:device_id`).
- Add a validation task in tasks.md:
  - [ ] T029 Validate device IDs use composite format in all data storage and retrieval logic

---

## HIGH Issues

### 3. Air Quality Metrics (PM2.5, VOC, CO2)
- In spec.md, clarify if these metrics are out of scope or add them to requirements.
- In tasks.md, add tasks for collecting and validating PM2.5, VOC, and CO2 readings if in scope:
  - [ ] T030 Implement PM2.5, VOC, CO2 data retrieval in source/collectors/amazon_collector.py
  - [ ] T031 Validate PM2.5, VOC, CO2 readings and store in SQLite

### 4. Fallback to Home Assistant Integration
- Add acceptance criteria for fallback logic in spec.md.
- In tasks.md, add a test task:
  - [ ] T032 [P] Create unit/integration test for Home Assistant fallback in tests/test_amazon_collector.py

### 5. Ambiguity (“NEEDS CLARIFICATION”)
- Specify Python version (e.g., Python 3.10+), storage (SQLite), and testing framework (pytest) in technical context and requirements.

### 6. Duplication (Retry Logic)
- Consolidate retry logic into a single requirement in spec.md.
- Reference this requirement in plan.md and tasks.md instead of repeating details.

---

## MEDIUM Issues

### 7. Terminology Drift
- Standardize to “device accessibility” throughout all documents.

### 8. Edge Case — Partial Data Retrieval
- Add a task:
  - [ ] T033 Handle partial data retrieval (temperature or humidity missing) and log appropriately

### 9. Duplicate Timestamp Detection
- Add a validation task:
  - [ ] T034 Validate and flag duplicate timestamps per device in source/storage/manager.py

### 10. Required Field Validation
- Add a validation task:
  - [ ] T035 Validate required fields (device_id, sensor_type, value, unit, timestamp) in all readings

---

## LOW Issues

### 11. Storage Manager Terminology
- Replace “database manager” and “SQLite schema” with “storage manager” for consistency.

### 12. Logging Task Redundancy
- Merge logging tasks into a single cross-phase logging utility task, referencing all relevant phases.

---

## Next Steps
- Apply these edits to spec.md, plan.md, and tasks.md as appropriate.
- Review with stakeholders before implementation.
