# Home Temperature Monitoring - Project Constitution

## Project Overview

**Status**: Active Development  
**Type**: Quick and Dirty Data Collection  
**Last Updated**: 2025-11-18

### Purpose

Collect temperature readings from home IoT sensors (Philips Hue and Google Nest) and record them in a suitable format for future statistical analysis.

**Primary Goal**: Analyze heat retention and dissipation patterns to demonstrate correlation between external conditions (temperature, weather) and indoor heating efficiency. This data will provide objective evidence to the landlord that insulation and energy efficiency improvements are needed.

### Key Principles

1. **Quick and Dirty**: Prioritize working solutions over perfect architecture
2. **Data Collection Focus**: We care about collecting and storing data correctly, not analyzing it
3. **Sprint-Based Development**: Work in feature-based sprints with stories and tasks
4. **Format Matters**: Data must be stored in a format suitable for future analysis

## Scope

### In Scope
- ✅ Collecting temperature readings from Philips Hue sensors
- ✅ Collecting temperature readings from Google Nest devices
- ✅ Collecting outside temperature from aggregate weather API services
- ✅ Storing data in SQLite database for efficient querying and analysis
- ✅ Timestamping and metadata for each reading
- ✅ Basic error handling and retry logic
- ✅ Scheduled/automated collection

### Out of Scope
- ❌ Data analysis and visualization (future project)
- ❌ Real-time alerting or monitoring
- ❌ Historical data migration
- ❌ User interface or dashboard
- ❌ Complex data transformations

## Data Sources

| Source | Device Type | Priority | API/Protocol |
|--------|-------------|----------|--------------|
| **Philips Hue** | Motion sensors (temperature capability) | High | Hue Bridge API (local/cloud) |
| **Google Nest** | Thermostats | High | Google Nest API / SDM API || **Weather API** | Outside temperature (aggregate service) | Medium | Weather API service (e.g., OpenWeatherMap, WeatherAPI) |
## Data Requirements

### Minimum Data Points Per Reading
- **Timestamp**: ISO 8601 format with timezone
- **Device ID**: Composite format `source_type:device_id` (e.g., `hue:sensor_abc123`, `nest:thermostat_xyz789`, `weather:outside`)
- **Temperature**: Celsius (standardized, metric only)
- **Location**: Room/zone identifier (or "outside" for weather data)
- **Device Type**: Hue sensor, Nest thermostat, or weather API

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
- **Day/Night indicator** (for outside readings) - based on sunrise/sunset times
- **Weather conditions** (for outside readings) - standardized index values
- Raw API response (for debugging)

## Technical Constraints

### Development Approach
- Use tools from available tech stack (Python preferred for rapid development)
- SQLite database for structured storage and efficient time-series queries
- Local execution on Mac Studio (no cloud deployment required)

### Performance Requirements
- Collection frequency: Every 5 minutes (288 readings/day per sensor) to accurately track heating/cooling cycles and occupancy mode transitions
- Flexible fallback to 10-15 minutes if API rate limits require adjustment
- Data retention: Indefinite (storage not a constraint)
- API rate limits must be respected
- Graceful degradation if devices offline

## Sprint Structure

### Sprint Numbering
- Sprints are numbered **S000**, **S001**, **S002**, etc.
- Tasks within sprints are numbered **T001**, **T002**, **T003**, etc. (sequential across all sprints)
- Each sprint has a branch named `sprint-N-name` (e.g., `sprint-0-foundation`)

### Sprint Definition
- **Duration**: Flexible (1-2 weeks typical)
- **Goal**: Deliver one complete feature
- **Components**: Multiple stories, each with tasks
- **Output**: Working, committed code + documentation
- **Branch**: Named `sprint-N-name` created from `main`
- **Documentation**: `specification.md` and `plan.md` in `sprints/sprint-N-name/`

### Sprint Workflow
1. **Planning**: Create sprint branch, write specification.md and plan.md using templates
2. **Task Compilation**: Create detailed task list from stories (tasks may optionally have individual task docs)
3. **Development**: Implement tasks on sprint branch
4. **Validation**: Verify deliverables meet acceptance criteria
5. **Merge**: Merge sprint branch to `main` when complete
6. **Retrospective**: Update plan.md with outcomes and learnings

### Templates
All planning documents use templates from `docs/templates/`:
- `sprint-specification.md` - Sprint requirements and design
- `sprint-plan.md` - Task list and progress tracking
- `task.md` - Individual task documentation (optional, for complex tasks)

### Definition of Done (per Sprint)
- [ ] Feature implemented and tested
- [ ] Code committed to git
- [ ] Documentation updated
- [ ] Data collection verified working
- [ ] No breaking changes to existing data format

## Development Workflow

### Branch Strategy
- `main`: Stable, working code
- `sprint-0-foundation`: Sprint 0 development
- `sprint-1-hue`: Sprint 1 development  
- `sprint-2-nest`: Sprint 2 development
- `sprint-3-automation`: Sprint 3 development
- `sprint-4-quality`: Sprint 4 development
- `sprint-5-polish`: Sprint 5 development (optional)
- `hotfix/*`: Quick fixes for broken collection

Each sprint branch is created from `main` and merged back when sprint deliverables are complete.

### Commit Standards
- Descriptive messages
- Reference sprint/story/task if applicable
- Working code only (or clearly marked WIP)

### Testing Standards
- Manual verification acceptable (quick and dirty)
- At minimum: verify data collection produces valid output
- Check API authentication works
- Confirm data format consistency

## File Structure (Proposed)

```
HomeTemperatureMonitoring/
├── docs/
│   ├── project-constitution.md (this file)
│   ├── tech-stack.md
│   └── templates/
│       ├── sprint-specification.md
│       ├── sprint-plan.md
│       └── task.md
├── sprints/
│   ├── sprint-0-foundation/  (S000)
│   │   ├── specification.md
│   │   ├── plan.md
│   │   └── tasks/ (optional)
│   │       ├── T001.md
│   │       └── T002.md
│   ├── sprint-1-hue/  (S001)
│   │   ├── specification.md
│   │   └── plan.md
│   ├── sprint-2-nest/  (S002)
│   │   ├── specification.md
│   │   └── plan.md
│   ├── sprint-3-automation/  (S003)
│   │   ├── specification.md
│   │   └── plan.md
│   └── sprint-4-quality/  (S004)
│       ├── specification.md
│       └── plan.md
├── source/
│   ├── collectors/
│   │   ├── hue_collector.py
│   │   └── nest_collector.py
│   ├── storage/
│   │   └── data_writer.py
│   └── scheduler/
│       └── collection_scheduler.py
├── data/
│   └── readings/
│       └── YYYY-MM-DD.csv (or similar)
├── config/
│   ├── config.yaml
│   └── secrets.yaml (gitignored)
├── tests/
│   └── (basic tests)
├── Makefile
├── requirements.txt
└── README.md
```

### Sprint Documentation Structure

Each sprint folder contains:
- **specification.md**: Detailed requirements, acceptance criteria, and technical design (from template)
- **plan.md**: Task breakdown, time estimates, dependencies, and progress tracking (from template)
- **tasks/** (optional): Individual task documentation for complex tasks (from template)

## Project Sprints

### Sprint 0: Project Foundation
**Goal**: Establish project structure and core architecture  
**Duration**: 1-2 days

**Stories**:
1. **Project Scaffolding**
   - Create directory structure (src/, data/, config/, tests/)
   - Set up Python virtual environment
   - Create requirements.txt with initial dependencies
   - Initialize Makefile with common tasks
   - Create README.md with setup instructions

2. **Configuration Management**
   - Define config.yaml schema (collection intervals, data paths)
   - Create secrets.yaml.example template
   - Implement config loader utility
   - Add .gitignore for secrets and data files

3. **Data Format Definition**
   - Define unified data schema (CSV columns or JSON structure)
   - Create sample data file with headers
   - Document data dictionary
   - Establish file naming convention (timestamps, rotation)

**Deliverables**: Working project skeleton, documented data format

---

### Sprint 1: Philips Hue Integration
**Goal**: Collect temperature data from Philips Hue motion sensors  
**Duration**: 3-5 days

**Stories**:
1. **Hue Bridge Discovery & Authentication**
   - Discover Hue Bridge on local network (mDNS or manual IP)
   - Implement Bridge button press authentication flow
   - Generate and securely store API key
   - Test connection to Bridge

2. **Sensor Discovery & Enumeration**
   - Query all sensors from Bridge
   - Filter for sensors with temperature capability
   - Map sensors to room/location names
   - Store sensor metadata (ID, name, type, location)

3. **Temperature Data Collection**
   - Implement temperature reading from each sensor
   - Convert to Celsius if needed
   - Add timestamp and metadata
   - Handle sensor offline/unavailable scenarios

4. **Data Storage**
   - Implement CSV writer (or JSON if preferred)
   - Write readings with proper format
   - Handle file rotation (daily/weekly files)
   - Verify data integrity

**Deliverables**: Working Hue collector storing timestamped temperature data

---

### Sprint 2: Google Nest Integration
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

### Sprint 3: Automation & Scheduling
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

### Sprint 4: Data Quality & Validation
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

### Sprint 5: Polish & Maintenance (Optional/Future)
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

**Critical Path** (Must Complete):
1. Sprint 0 → Sprint 1 → Sprint 2 → Sprint 3 → Sprint 4

**Parallel Opportunities**:
- Sprint 1 and Sprint 2 could potentially be parallelized if working with multiple people
- Sprint 4 stories can begin during Sprint 3 (validation on early data)

**Flexibility**:
- Sprint 5 is optional/ongoing maintenance
- Can pause after Sprint 3 if automation is working well
- Can extend any sprint if complexity discovered

# Sprint Planning Structure

- Sprint 0: Project Foundation
  - Setup, configuration, schema, documentation
- Sprint 1: Philips Hue integration
- Sprint 2: Nest integration
- Sprint 3: Weather API integration
- Sprint 4+: Data analysis, reporting, enhancements

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
1. ✅ Temperature data is collected from both Philips Hue and Google Nest
2. ✅ Data is stored in a consistent, analysis-ready format
3. ✅ Collection runs automatically on a schedule
4. ✅ System recovers gracefully from temporary failures
5. ✅ Data format is documented and stable

## API & Authentication Notes

### Philips Hue
- Requires local network access to Hue Bridge
- Authentication via Bridge button press + API key generation
- Local API preferred (no cloud dependency)
- Rate limits: Generous for local polling

### Google Nest
- Requires Google Cloud project setup
- OAuth 2.0 authentication
- Smart Device Management (SDM) API
- Rate limits: Check current quotas
- May require subscription ($5 one-time for SDM API access)

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
- Quick and dirty acceptable
- Code should be understandable in 6 months
- Minimal dependencies

---

**Next Steps**: Create Sprint 1 planning document and begin implementation.

