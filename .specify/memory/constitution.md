<!--
Sync Impact Report
Version change: 1.0.0 → 1.1.0 (MINOR: full rewrite to project-specific principles)
Modified principles: All (template → project rules)
Added sections: Scope, Data Requirements, Technical Constraints, Sprint Structure, Development Workflow, Success Criteria, API & Auth Notes, Non-Functional Requirements
Removed sections: None
Templates requiring updates: plan-template.md ✅, spec-template.md ✅, tasks-template.md ✅
Follow-up TODOs: None
-->

# Home Temperature Monitoring Constitution

## Core Principles

### I. Quick and Dirty
Prioritize working solutions over perfect architecture. Deliver value rapidly, accept technical debt if it accelerates data collection.  
Rationale: Speed is essential for evidence gathering; refactoring can follow if needed.

### II. Data Collection Focus
The project MUST focus on collecting and storing data correctly, not analyzing it. All code and tasks should serve the goal of reliable, validated data acquisition.  
Rationale: Analysis is explicitly out of scope; future projects will handle it.

### III. Sprint-Based Development
Work is organized in feature-based sprints, each with stories and tasks. Sprints MUST produce working code and documentation.  
Rationale: Enables incremental delivery and clear progress tracking.

### IV. Format Matters
Data MUST be stored in a format suitable for future analysis (SQLite preferred, CSV acceptable for prototypes).  
Rationale: Ensures collected data is usable for statistical analysis and advocacy.

## Scope

### In Scope
- Collect temperature readings from Philips Hue sensors
- Collect temperature readings from Google Nest devices
- Collect outside temperature from aggregate weather API services
- Store data in SQLite database for efficient querying and analysis
- Timestamping and metadata for each reading
- Basic error handling and retry logic
- Scheduled/automated collection

### Out of Scope
- Data analysis and visualization (future project)
- Real-time alerting or monitoring
- Historical data migration
- User interface or dashboard
- Complex data transformations

## Data Requirements

- Timestamp: ISO 8601 format with timezone
- Device ID: Composite format `source_type:device_id` (e.g., `hue:sensor_abc123`)
- Temperature: Celsius (standardized, metric only)
- Location: Room/zone identifier (or "outside" for weather data)
- Device Type: Hue sensor, Nest thermostat, or weather API
- Indoor temp range: 0°C to 40°C (flag anomalies)
- Outside temp range: -40°C to 50°C
- Duplicate timestamp detection per device
- Required field presence validation
- Weather conditions index: standardized categorical values (see project docs)
- Optional metadata: humidity, battery, signal, thermostat mode/state, day/night indicator, raw API response

## Technical Constraints

- Python preferred for rapid development
- Use Virtualenv for dependency management
- SQLite database for structured storage
- Local execution on Mac Studio (no cloud deployment)
- Collection frequency: Every 5 minutes (flexible to 10-15 if rate limited)
- Data retention: Indefinite
- API rate limits must be respected
- Graceful degradation if devices offline

## Sprint Structure

- Sprints numbered S000, S001, S002, etc.
- Tasks numbered T001, T002, ... sequentially across sprints
- Each sprint has a branch named `sprint-N-name`
- Sprint docs: specification.md and plan.md in sprint folder
- Definition of Done: Feature implemented/tested, code committed, docs updated, data collection verified, no breaking changes to data format

## Development Workflow

- Branch strategy: `main` for stable code, `sprint-N-name` for sprint work, `hotfix/*` for urgent fixes
- Commit standards: Descriptive messages, reference sprint/story/task, working code only (or marked WIP)
- Testing standards: Manual verification acceptable, verify data collection output, check API auth, confirm data format consistency

## Success Criteria

- Temperature data collected from both Philips Hue and Google Nest
- Data stored in consistent, analysis-ready format
- Collection runs automatically on schedule
- System recovers gracefully from temporary failures
- Data format documented and stable

## API & Authentication Notes

- Philips Hue: Local network access, Bridge button press + API key, local API preferred
- Google Nest: Google Cloud project, OAuth 2.0, SDM API, rate limits, $5 one-time fee

## Non-Functional Requirements

- Security: API keys/secrets in gitignored config, no hardcoded credentials, local network only
- Reliability: Acceptable to miss occasional readings, must not crash on API failures, retry policy (3 attempts, exponential backoff), log failures and continue
- Maintainability: Quick and dirty acceptable, code understandable in 6 months, minimal dependencies

## Governance

- This constitution supersedes all other practices for this project.
- Amendments require documentation, approval, and migration plan.
- All sprints, plans, and specs must verify compliance with principles and constraints.
- Any complexity or deviation must be justified in sprint documentation.
- Versioning: MAJOR for principle removals/redefinitions, MINOR for new principles/sections, PATCH for clarifications/typos.
- Compliance review at each sprint retrospective.

**Version**: 1.1.0 | **Ratified**: 2025-11-18 | **Last Amended**: 2025-11-18