# Home Temperature Monitoring - Project Constitution

## Project Overview

**Project Name**: Home Temperature Monitoring
**Status**: Active Development  
**Current Sprint**: Sprint 5 - System Reliability (In Progress)  
**Completed Sprints**: 0 (Foundation), 1 (Hue), 4 (Amazon AQM)  
**Last Updated**: 2025-11-20

---

## ⚠️ Critical Reminders for AI Agents

1. **ALWAYS ACTIVATE PYTHON VENV FIRST**: `source venv/bin/activate` before any Python commands
2. **VERIFY TECH STACK OPTIONS**: Review `docs/tech-stack.md` - we have Python, Swift, C/C++, Node.js available
3. **TEST-DRIVEN DEVELOPMENT**: Write tests before implementation (not 'quick and dirty' anymore)
4. **RESEARCH COMPLEX FEATURES**: Document research in research.md (see Sprint 4 example)

---

### Purpose

Collect temperature and air quality readings from home IoT sensors (Philips Hue, Amazon Alexa Air Quality Monitor, and Google Nest) and record them in a suitable format for future statistical analysis.

**Primary Goal**: Analyze heat retention and dissipation patterns to demonstrate correlation between external conditions (temperature, weather) and indoor heating efficiency. This data will provide objective evidence to the landlord that insulation and energy efficiency improvements are needed.

### Key Principles

1. **Test-Driven Development**: Unit tests guide implementation (evolved from 'quick and dirty' after Sprint 4 complexity)
2. **Research-Driven**: Complex features require research logs, experimentation, and iteration (see `specs/004-alexa-aqm-integration/research.md`)
3. **Data Collection Focus**: We care about collecting and storing data correctly, not analyzing it
4. **Sprint-Based Development**: Work in feature-based sprints with comprehensive specs
5. **Format Matters**: Data must be stored in a format suitable for future analysis
6. **Tech Stack Diversity**: Consider full tech stack options (Python, Swift, C/C++, Node.js) - see `docs/tech-stack.md`

## Scope

### In Scope
- ✅ Collecting temperature readings from Philips Hue sensors (IMPLEMENTED)
- ✅ Collecting air quality and temperature readings from Amazon Alexa Air Quality Monitor (IMPLEMENTED)
- ⏳ Collecting temperature readings from Google Nest devices (PLANNED)
- ⏳ Collecting outside temperature from aggregate weather API services (PLANNED)
- ✅ Storing data in SQLite database for efficient querying and analysis (IMPLEMENTED)
- ✅ Timestamping and metadata for each reading (IMPLEMENTED)
- ⏳ Comprehensive error handling and retry logic (IN PROGRESS - Sprint 5)
- ⏳ Automated scheduled collection (PARTIAL - collector code ready, scheduling pending)

### Out of Scope
- ❌ Data analysis and visualization (future project)
- ❌ Real-time alerting or monitoring
- ❌ Historical data migration
- ❌ User interface or dashboard
- ❌ Complex data transformations

## Data Sources

| Source | Device Type | Priority | API/Protocol | Status |
|--------|-------------|----------|--------------|--------|
| **Philips Hue** | Motion sensors (temperature capability) | High | Hue Bridge API (local) | ✅ Implemented |
| **Amazon Alexa Air Quality Monitor** | Air quality and temperature monitor | High | GraphQL API via Amazon | ✅ Implemented |
| **Google Nest** | Thermostats | High | Google Nest API / SDM API | ⏳ Planned |
| **Weather API** | Outside temperature (aggregate service) | Medium | Weather API service | ⏳ Planned |
## Data Requirements

### Minimum Data Points Per Reading
- **Timestamp**: ISO 8601 format with timezone
- **Device ID**: Composite format `source_type:device_id` (e.g., `hue:sensor_abc123`, `alexa:monitor_def456`, `nest:thermostat_xyz789`, `weather:outside`)
- **Temperature**: Celsius (standardized, metric only)
- **Location**: Room/zone identifier (or "outside" for weather data)
- **Device Type**: Hue sensor, Alexa air quality monitor, Nest thermostat, or weather API

### Data Quality Validation
- **Indoor temperature range**: 0°C to 40°C (readings outside this range flagged as anomalous)
- **Outside temperature range**: -40°C to 50°C (weather data has wider acceptable range)
- Duplicate timestamp detection per device
- Required field presence validation

### Weather Conditions Index (Standardized)
For outside temperature readings, record weather conditions using consistent categorical values:

**Primary Conditions** (mutually exclusive for sky state):
- `sunny` - Clear skies, minimal cloud cover
- `cloudy` - Overcast or significant cloud cover

**Precipitation** (can combine with primary):
- `raining` - Rain or drizzle
- `snowing` - Snow or sleet

**Wind** (can combine with any):
- `windy` - Significant wind (threshold TBD by weather API)

**Combination Format**: Pipe-separated (e.g., `cloudy|raining`, `sunny|windy`, `cloudy|snowing|windy`)

**Day/Night Indicator**: Boolean or categorical (`day`, `night`) based on local sunrise/sunset times

### Optional Metadata
- Humidity (if available)
- Battery level (for sensors)
- Signal strength/connectivity status
- Thermostat mode (heating/cooling/off/away) - critical for cycle analysis
- Thermostat state (actively heating/cooling vs idle)
- **Air quality metrics**: PM2.5, PM10, VOC (volatile organic compounds), CO2 equivalent (ppm)
- **Air quality index**: Standardized AQI (0-500 scale) or device-specific rating
- **Day/Night indicator** (for outside readings) - based on sunrise/sunset times
- **Weather conditions** (for outside readings) - standardized index values
- Raw API response (for debugging)

## Technical Constraints

### Development Approach
- **CRITICAL**: Always activate Python virtual environment before running code: `source venv/bin/activate`
- Consider full tech stack options (see `docs/tech-stack.md`): Python, Swift, C/C++, Node.js
- Python preferred for data collection, but evaluate alternatives for performance-critical code
- SQLite database for structured storage and efficient time-series queries
- Local execution on Mac Studio M2 Ultra (128GB RAM, 60-core GPU via Metal)

### Performance Requirements
- Collection frequency: Every 5 minutes (288 readings/day per sensor) to accurately track heating/cooling cycles and occupancy mode transitions
- Flexible fallback to 10-15 minutes if API rate limits require adjustment
- Data retention: Indefinite (storage not a constraint)
- API rate limits must be respected
- Graceful degradation if devices offline

## Sprint Structure

### Sprint Numbering
- Sprints are numbered **001**, **002**, **003**, etc. (zero-padded)
- Branch naming: `NNN-short-name` (e.g., `001-project-foundation`)
- Spec directories: `specs/NNN-name/` (e.g., `specs/001-project-foundation/`)
- Each sprint corresponds to one feature/capability

### Sprint Definition
- **Duration**: Flexible (3-7 days typical)
- **Goal**: Deliver one complete, testable feature
- **Components**: User stories, functional requirements, acceptance criteria
- **Output**: Working code + tests + documentation
- **Branch**: Named `NNN-short-name` created from `master`
- **Documentation**: Comprehensive spec in `specs/NNN-name/`
- **Merge**: Via Pull Request with code review

### Sprint Workflow
1. **Planning**: Create sprint branch, write spec.md and plan.md
2. **Research**: Investigate APIs, document findings in research.md (critical for complex features)
3. **Test Design**: Write test cases based on acceptance criteria (TDD approach)
4. **Implementation**: Implement features to pass tests (iterate: test → code → refine)
5. **Validation**: Verify deliverables meet acceptance criteria, run full test suite
6. **Code Review**: Self-review or automated analysis before merge
7. **Merge**: Merge to `master` via Pull Request
8. **Retrospective**: Update plan.md with outcomes, learnings, and metrics

### Documentation Templates
All spec documents follow a consistent structure:
- **spec.md**: User scenarios, requirements, success criteria, edge cases
- **plan.md**: Implementation plan, task breakdown, dependencies
- **research.md**: API research, technical investigation
- **data-model.md**: Database schema, data structures
- **quickstart.md**: Quick reference and usage guide
- Template reference: `docs/spec-structure-reference.md`

### Definition of Done (per Sprint)
- [ ] Unit tests written and passing (minimum 80% coverage for new code)
- [ ] Feature implemented following TDD approach
- [ ] All tests passing in Python venv: `pytest tests/`
- [ ] Research documented in research.md (if complex feature)
- [ ] Code committed to git with descriptive messages
- [ ] Documentation updated (spec.md, plan.md, quickstart.md)
- [ ] Data collection verified working in real environment
- [ ] No breaking changes to existing data format or API contracts
- [ ] Security review completed (credentials, secrets, API exposure)

## Development Workflow

### Development Environment Setup

**CRITICAL - Python Virtual Environment**:
```bash
# ALWAYS activate venv before running Python code
source venv/bin/activate

# Verify activation (should show venv path)
which python
# Expected: /Users/peternicholls/Dev/HomeTemperatureMonitoring/venv/bin/python

# Install/update dependencies
pip install -r requirements.txt
```

**Why This Matters**:
- Running Python without venv wastes tokens and time with dependency errors
- Tests fail when run outside venv
- Package installations go to wrong location
- AI agents frequently forget this step - always check first!

**Tech Stack Reference**: See `docs/tech-stack.md` for full options (Python, Swift, C/C++, Node.js)

### Branch Strategy
- `master`: Stable, production-ready code (default branch)
- `NNN-short-name`: Feature branches (e.g., `001-project-foundation`, `002-hue-integration`)
- Feature branches created from `master` and merged via Pull Request when complete
- Each feature corresponds to a spec in `specs/NNN-name/`

**Completed Branches** (merged to master):
- `001-project-foundation` ✅
- `002-hue-integration` ✅  
- `004-alexa-aqm-integration` ✅

**Active Branch**:
- `005-system-reliability` ⏳

### Commit Standards
- Descriptive messages
- Reference sprint/story/task if applicable
- Working code only (or clearly marked WIP)

### Testing Standards
- **Approach**: Test-Driven Development (TDD) - write tests before implementation
- **Unit Tests**: 33 total tests (18 Hue + 15 Amazon AQM)
- **Test Framework**: pytest with async support and comprehensive mocking
- **Mocking**: Comprehensive mocking for external APIs (avoid actual API calls in tests)
- **Coverage**: Focus on critical paths (authentication, data collection, storage)
- **Manual Testing**: Used for integration validation and exploratory testing
- **Evaluation Framework**: Automated evaluation with test datasets (see `evaluation.py`)
- **Research Log**: Complex features require research documentation (see Sprint 4 example)
- **Iteration**: Expect multiple cycles of research → experiment → test → refine

## File Structure (Current Implementation)

```
HomeTemperatureMonitoring/
├── docs/
│   ├── project-outliner.md (this file)
│   ├── tech-stack.md
│   ├── evaluation-framework.md
│   ├── credential-rotation-guide.md
│   ├── hue-authentication-guide.md
│   └── code-review-system-reliability.md
├── specs/  (sprint documentation)
│   ├── 001-project-foundation/
│   ├── 002-hue-integration/
│   ├── 003-system-reliability/
│   ├── 004-alexa-aqm-integration/
│   └── 005-system-reliability/  (verification sprint)
├── source/
│   ├── collectors/
│   │   ├── hue_auth.py
│   │   ├── hue_collector.py
│   │   ├── amazon_auth.py
│   │   ├── amazon_collector.py
│   │   └── amazon_aqm_collector_main.py
│   ├── storage/
│   │   ├── manager.py  (SQLite database manager)
│   │   └── schema.py   (database schema definitions)
│   ├── config/
│   │   ├── loader.py
│   │   └── validator.py
│   ├── utils/
│   │   └── logging.py
│   ├── web/
│   │   ├── app.py  (Flask web interface)
│   │   └── templates/
│   ├── evaluation.py
│   └── verify_setup.py
├── data/
│   ├── temperature_readings.db  (SQLite database)
│   └── evaluation_*.json(l)  (evaluation datasets)
├── config/
│   ├── config.yaml
│   ├── secrets.yaml (gitignored)
│   └── secrets.yaml.example
├── tests/
│   ├── test_hue_collector.py
│   ├── test_amazon_aqm.py
│   └── manual/
├── logs/  (application logs)
├── Makefile
├── requirements.txt
├── pytest.ini
└── README.md
```

### Sprint Documentation Structure

Each spec folder (`specs/NNN-name/`) contains:
- **spec.md**: Feature requirements and user scenarios
- **plan.md**: Implementation plan and task breakdown
- **research.md**: Technical research and API documentation
- **data-model.md**: Data structures and database schema
- **quickstart.md**: Quick reference guide
- **checklists/**: Quality validation checklists
- **contracts/**: API contracts and interfaces
- **tasks.md**: Detailed task list with status tracking

## Project Sprints

### Completed Sprints

**Sprint 0: Project Foundation** ✅  
Established project structure, configuration management (config.yaml, secrets), SQLite database schema, and data format definition. See `specs/001-project-foundation/` for details.

**Sprint 1: Philips Hue Integration** ✅  
Implemented Hue Bridge authentication, sensor discovery, and temperature data collection with 18 unit tests. See `specs/002-hue-integration/` for details.

**Sprint 4: Amazon Alexa Air Quality Monitor Integration** ✅  
Integrated Amazon AQM with GraphQL API, OAuth authentication, async collectors, and comprehensive air quality metrics (PM2.5, PM10, VOC, CO2e). 15 unit tests, 5 security vulnerabilities fixed. See `specs/004-alexa-aqm-integration/` for details.

---

### Sprint 5: System Reliability IN PROGRESS
**Goal**: Enhance system reliability, monitoring, and error handling  
**Duration**: 3-4 days

**Stories**:
1. **Enhanced Error Handling**
   - Implement comprehensive exception handling for all API calls
   - Add circuit breaker pattern for failing data sources
   - Create error classification (transient vs permanent failures)
   - Implement graceful degradation for partial system failures

2. **Health Monitoring & Alerting**
   - Create health check endpoint/script for system status
   - Monitor collection success rates per device
   - Track API response times and timeouts
   - Implement basic alerting for prolonged failures (email/log)

3. **Data Integrity Verification**
   - Add checksums or validation hashes for database records
   - Implement automatic gap detection in time series
   - Create data completeness reports (% uptime per device)
   - Add database integrity checks on startup

4. **Collection Metrics & Observability**
   - Track and log collection statistics (readings/hour, failures/hour)
   - Create daily summary reports (devices collected, gaps, errors)
   - Add performance metrics (API latency, database write times)
   - Implement structured logging with log levels

**Deliverables**: Robust system with comprehensive monitoring, error handling, and data integrity verification

---

### Sprint 6: Google Nest Integration
**Goal**: Collect temperature data from Google Nest thermostats  
**Duration**: 4-6 days

**Stories**:
1. **Google Cloud Project Setup**
   - Create Google Cloud project
   - Enable Smart Device Management API
   - Pay SDM API access fee ($5 one-time)
   - Configure OAuth 2.0 credentials

2. **OAuth Authentication Flow**
   - Implement OAuth 2.0 device/web flow
   - Handle token storage and refresh
   - Test authentication with Nest account
   - Document authentication process

3. **Device Discovery & Enumeration**
   - Query Nest devices via SDM API
   - Filter for thermostats
   - Map devices to location names
   - Store device metadata (ID, name, location, type)

4. **Temperature Data Collection**
   - Implement temperature reading from each thermostat
   - Extract current temperature (not setpoint)
   - Handle multiple temperature sensors if available
   - Add humidity if available

5. **Unified Data Integration**
   - Merge Nest data with Hue data format
   - Ensure consistent timestamp format
   - Add device type/source identifier
   - Test combined data output

**Deliverables**: Working Nest collector integrated with Hue data

---

### Sprint 7: Automation & Scheduling
**Goal**: Automated periodic data collection with reliability  
**Duration**: 3-4 days

**Stories**:
1. **Collection Orchestrator**
   - Create main collection script
   - Call both Hue and Nest collectors
   - Coordinate timing and sequencing
   - Handle partial failures gracefully

2. **Scheduling Implementation**
   - Choose scheduling method (launchd on macOS)
   - Create launchd plist configuration
   - Set collection interval (5-15 minutes)
   - Test scheduled execution
   - Document manual trigger method

3. **Error Handling & Resilience**
   - Implement retry logic for API failures: 3 attempts with exponential backoff (1s, 2s, 4s)
   - Exponential backoff for rate limits
   - Continue collection if one source fails
   - Prevent duplicate readings

4. **Logging & Monitoring**
   - Set up Python logging framework
   - Log collection successes and failures
   - Log API errors and retries
   - Create log rotation policy
   - Add collection statistics (readings/hour)

**Deliverables**: Automated collection running on schedule with proper error handling

---

### Sprint 8: Data Quality & Validation
**Goal**: Ensure data integrity and prepare for analysis  
**Duration**: 2-3 days

**Stories**:
1. **Data Validation**
   - Validate temperature ranges (reasonable values)
   - Check for duplicate timestamps
   - Verify all required fields present
   - Detect and flag anomalies (sensor failures)

2. **Data Quality Reporting**
   - Create data completeness report script
   - Calculate collection success rate per device
   - Identify gaps in data collection
   - Generate summary statistics

3. **Storage Optimization** (if needed)
   - Evaluate CSV vs SQLite vs other formats
   - Migrate to database if file size becomes issue
   - Implement data compression if needed
   - Ensure backward compatibility

4. **Documentation & Handoff**
   - Document data schema thoroughly
   - Create data dictionary with field descriptions
   - Document known data quality issues
   - Prepare data for analysis handoff
   - Create example analysis queries/scripts

**Deliverables**: Validated, documented data ready for statistical analysis

---

### Sprint 9: Polish & Maintenance (Optional/Future)
**Goal**: Production readiness and long-term maintenance  
**Duration**: Ongoing

**Potential Stories**:
- Add unit tests for critical functions
- Create backup/archival strategy
- Monitor disk space usage
- Add data export utilities (different formats)
- Create simple data viewer (CLI tool)
- Implement data anonymization if sharing
- Add configuration hot-reload
- Create diagnostic/health check script

**Deliverables**: Production-ready system with maintenance tools

---

## Sprint Sequencing

**Completed** ✅:
- Sprint 0 (Project Foundation)
- Sprint 1 (Philips Hue Integration)
- Sprint 4 (Amazon AQM Integration)

**In Progress** ⏳:
- Sprint 5 (System Reliability)

**Planned**:
- Sprint 6 (Google Nest Integration)
- Sprint 7 (Automation & Scheduling)
- Sprint 8 (Data Quality & Validation)
- Sprint 9 (Polish & Maintenance - Optional)

**Notes**:
- Nest integration (Sprint 6) and Weather API integration deferred pending system reliability completion
- Sprint 7 automation partially implemented; full scheduling pending reliability improvements

## Current Sprint Status

**Active**: Sprint 5 (System Reliability) - In Progress ⏳  
**Last Completed**: Sprint 4 (Amazon AQM Integration) - Merged to master ✅  
**Next Planned**: See `NEXT_SPRINT_ROADMAP.md` for strategic options

## Clarifications

### Session 2025-11-18

- Q: What storage format should be used for temperature readings (CSV, JSON, SQLite, or hybrid)? → A: B (SQLite database)
- Q: What should the data collection frequency be (5, 10, or 15 minutes)? → A: 5 minutes preferred for tracking heating/cooling cycles and occupancy transitions; flexible if API limits require adjustment
- Q: What temperature range should be considered valid for indoor readings (validation bounds)? → A: B (0°C to 40°C) - realistic indoor extremes for data quality validation
- Q: What retry policy should be used for failed API calls (number of retries and backoff strategy)? → A: B (3 retries with exponential backoff)
- Q: What format should device identifiers use to ensure uniqueness across sources? → A: B (Composite: source_type:device_id, e.g., `hue:sensor_abc123`, `nest:thermostat_xyz789`, `weather:outside`)
- Q: Should outside temperature collection include additional weather context (day/night, conditions)? \u2192 A: Yes - record day/night indicator and standardized weather conditions (sunny, cloudy, raining, snowing, windy, and combinations) to analyze correlation with indoor heat retention/dissipation patterns

## Success Criteria

The project is successful when:
1. ✅ Temperature data is collected from Philips Hue sensors
2. ✅ Air quality and temperature data collected from Amazon AQM
3. ⏳ Temperature data collected from Google Nest thermostats (pending)
4. ✅ Data is stored in SQLite database in analysis-ready format
5. ⏳ Collection runs automatically on a schedule (partial implementation)
6. ⏳ System recovers gracefully from temporary failures (in progress)
7. ✅ Data format is documented and stable

## API & Authentication Notes

### Philips Hue (IMPLEMENTED ✅)
- Local network access to Hue Bridge
- Authentication: Bridge button press + API key generation
- API key stored in `secrets.yaml`
- Local API only (no cloud dependency)
- Implementation: `source/collectors/hue_auth.py`, `hue_collector.py`
- Guide: `docs/hue-authentication-guide.md`

### Amazon Alexa Air Quality Monitor (IMPLEMENTED ✅)
- GraphQL API via Amazon Web Services
- OAuth 2.0 authentication (LWA - Login with Amazon)
- Tokens stored in `secrets.yaml` with auto-refresh
- Implementation: `source/collectors/amazon_auth.py`, `amazon_collector.py`
- Async/await pattern for efficient data collection
- Guide: `docs/Amazon-Alexa-Air-Quality-Monitoring/`

### Google Nest (PLANNED ⏳)
- Google Cloud project setup required
- OAuth 2.0 authentication
- Smart Device Management (SDM) API
- $5 one-time SDM API access fee
- Rate limits: TBD based on quotas

## Non-Functional Requirements

### Security
- API keys/secrets in gitignored config files
- No hardcoded credentials
- Local network only (no external exposure needed)

### Reliability
- Acceptable to miss occasional readings
- Must not crash on API failures
- Retry policy: 3 attempts with exponential backoff (e.g., 1s, 2s, 4s delays)
- After retry exhaustion, log failure and continue to next scheduled collection
- Log errors for debugging

### Maintainability
- Test-driven development for reliability (evolved from 'quick and dirty')
- Code should be understandable in 6 months
- Minimal dependencies per language ecosystem
- Consider tech stack alternatives for performance-critical code (see `docs/tech-stack.md`)

### Performance
- Profile before optimizing (measure actual bottlenecks)
- Consider Swift/C++ for performance-critical paths (Core ML, Metal GPU acceleration)
- Leverage Mac Studio M2 Ultra capabilities (128GB RAM, 60-core GPU)
- Python default unless profiling shows need for compiled languages

---

**Project Status**: Active development on Sprint 5 (System Reliability)
**Last Updated**: 2025-11-20
**For Strategic Planning**: See `NEXT_SPRINT_ROADMAP.md`

