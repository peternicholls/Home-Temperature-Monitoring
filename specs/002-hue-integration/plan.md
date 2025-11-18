# Implementation Plan: Philips Hue Temperature Collection

**Branch**: `002-hue-integration` | **Date**: 2025-11-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-hue-integration/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Collect temperature data from Philips Hue motion sensors and store in SQLite database. System authenticates with Hue Bridge on local network, discovers temperature-capable sensors, collects readings every 5 minutes, and stores data with timestamps and metadata for future analysis.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: NEEDS CLARIFICATION (Hue API client library selection)  
**Storage**: SQLite database (as per constitution)  
**Testing**: pytest (manual verification acceptable per constitution)  
**Target Platform**: macOS (Mac Studio, local execution)  
**Project Type**: Single project (data collection script)  
**Performance Goals**: <10 seconds per collection cycle, 5-minute collection interval (288 readings/day per sensor)  
**Constraints**: Local network only, API rate limits must be respected, graceful degradation if sensors offline  
**Scale/Scope**: ~5-10 Hue sensors, indefinite data retention, single-user local deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Pre-Research) ✅ PASSED

### Principle Compliance

✅ **Quick and Dirty**: Using simple Python scripts, local API access, manual authentication flow - prioritizes working solution  
✅ **Data Collection Focus**: Feature is exclusively about collecting and storing temperature data, no analysis components  
✅ **Sprint-Based Development**: Organized as Sprint 1 with clear stories and tasks in spec.md  
✅ **Format Matters**: Using SQLite database for structured storage as per constitution requirement  

### Scope Compliance

✅ **In Scope**: Collecting temperature from Philips Hue sensors - explicitly listed in constitution  
✅ **Out of Scope**: No analysis, no UI, no real-time alerting - correctly excluded  

### Technical Constraints Compliance

✅ **Python**: Using Python 3.11+ as preferred language  
✅ **SQLite**: Using SQLite database as specified  
✅ **Local Execution**: Mac Studio deployment, no cloud components  
✅ **Collection Frequency**: Targeting 5-minute intervals as specified  
✅ **API Rate Limits**: Will implement respectful polling, retry logic with exponential backoff  
✅ **Graceful Degradation**: Design handles offline sensors without failing entire collection  

### Data Requirements Compliance

✅ **Timestamp**: ISO 8601 with timezone - covered in FR-007  
✅ **Device ID**: Composite format `hue:sensor_id` - covered in FR-008  
✅ **Temperature**: Celsius conversion - covered in FR-006  
✅ **Location**: Room/zone identifier from sensor metadata - covered in FR-004  
✅ **Device Type**: `hue_sensor` type identifier - covered in FR-009  
✅ **Indoor Range Validation**: 0°C to 40°C with anomaly flagging - covered in FR-011  
✅ **Duplicate Detection**: Timestamp + device_id uniqueness - covered in FR-010  
✅ **Optional Metadata**: Battery level, signal strength - covered in FR-014  

### Non-Functional Requirements Compliance

✅ **Security**: API key in gitignored secrets.yaml, no hardcoded credentials - covered in FR-015  
✅ **Reliability**: Handles offline sensors, retry policy (3 attempts exponential backoff) - covered in FR-013  
✅ **Maintainability**: Python code, minimal dependencies, documented

**GATE STATUS**: ✅ **PASS** - All constitution requirements met, no violations to justify

---

### Post-Design Check (After Phase 1) ✅ PASSED

**Re-evaluated**: 2025-11-18 after completing research, data model, contracts, and quickstart

### Design Decisions Alignment

✅ **Library Choice (phue)**: Aligns with "quick and dirty" - simple, well-maintained, local API support  
✅ **Schema Design**: Single table with indexes - simple and analysis-ready, no over-engineering  
✅ **Authentication Flow**: One-time button press, stored credentials - straightforward, secure  
✅ **Error Handling**: 3 retries with exponential backoff - matches constitution exactly  
✅ **Discovery Method**: mDNS with manual fallback - pragmatic, handles network variations  
✅ **Location Mapping**: Config-based with Hue name fallback - flexible, user-friendly  
✅ **Validation Strategy**: Flag anomalies but store - preserves data, enables post-hoc analysis  

### No New Violations Introduced

- No additional complexity beyond requirements
- No scope creep (stayed focused on Hue collection only)
- No over-architecting (avoided async, avoided abstraction layers)
- Dependencies minimal (only `phue` library)
- Storage remains SQLite (no database migration)
- Testing remains manual verification (per constitution)

### Architecture Simplicity Maintained

**Database**: 1 table (`temperature_readings`) with 3 indexes - appropriate for use case  
**Modules**: 2 new files (`hue_collector.py`, `hue_auth.py`) - minimal footprint  
**Configuration**: Extends existing config system - no new config infrastructure  
**Secrets**: Uses existing secrets.yaml pattern - consistent with project  

**GATE STATUS**: ✅ **PASS** - Design adheres to constitution, no deviations introduced

---

## Edge Case Handling

*Documented approaches for edge cases identified in spec.md*

| Edge Case | Handling Approach | Implementation Reference |
|-----------|-------------------|-------------------------|
| Bridge IP address changes (DHCP) | Auto-discovery on connection failure; mDNS re-discovery with manual fallback | research.md Task 2, tasks.md T011-T012 |
| Temperature outside valid range (0-40°C) | Flag as anomalous but store with `is_anomalous=true`; log warning | research.md Task 4, tasks.md T030 |
| Database locked during write | Retry logic with exponential backoff in storage manager | tasks.md T039 |
| Malformed/incomplete API data | Validation with graceful error logging; skip malformed readings | tasks.md T033-T034 |
| Low battery/offline sensors | Detection via `reachable` flag; skip and continue with other sensors | tasks.md T034, spec.md FR-013 |
| Clock drift (system vs Bridge) | System clock authoritative for `timestamp`; Bridge `lastupdated` is metadata only | spec.md Edge Cases note |

**Design Principle**: All edge cases use non-blocking error handling—log and continue rather than fail the entire collection cycle.

## Project Structure

### Documentation (this feature)

```text
specs/002-hue-integration/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── hue-api-response-sample.json  # Example sensor response
│   ├── database-schema.sql           # Temperature readings table
│   ├── config-hue.yaml               # Hue configuration schema
│   └── secrets-hue.yaml.example      # Hue secrets template
├── spec.md              # Feature specification (already exists)
├── checklists/          # Requirements checklist (already exists)
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
source/
├── collectors/
│   ├── __init__.py
│   ├── hue_collector.py      # Main Hue collection logic
│   └── hue_auth.py            # Authentication & discovery
├── storage/
│   ├── __init__.py
│   ├── manager.py             # Database manager (already exists)
│   └── schema.py              # Schema definitions (already exists)
├── config/
│   ├── __init__.py
│   ├── loader.py              # Config loader (already exists)
│   └── validator.py           # Config validator (already exists)
└── utils/
    ├── __init__.py
    └── logging.py             # Logging utilities (already exists)

config/
├── config.yaml                # Updated with Hue settings
└── secrets.yaml               # Updated with Hue API key (gitignored)

tests/
├── test_hue_collector.py      # Hue collector tests
├── test_hue_auth.py           # Authentication tests
└── integration/
    └── test_hue_integration.py  # End-to-end collection test

data/
└── temperature.db             # SQLite database (created at runtime)
```

**Structure Decision**: Single project structure selected. Existing foundation from 001-project-foundation includes config, storage, and utils modules. This feature adds `collectors/` module for Hue-specific logic while reusing existing infrastructure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. This section is not applicable - all constitution requirements are met.
