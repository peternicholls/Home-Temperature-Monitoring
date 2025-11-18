# Home Temperature Monitoring - Project Constitution

## Project Overview

**Status**: Active Development  
**Type**: Quick and Dirty Data Collection  
**Last Updated**: 2025-11-18

### Purpose

Collect temperature readings from home IoT sensors (Philips Hue and Google Nest) and record them in a suitable format for future statistical analysis.

### Key Principles

1. **Quick and Dirty**: Prioritize working solutions over perfect architecture
2. **Data Collection Focus**: We care about collecting and storing data correctly, not analyzing it
3. **Sprint-Based Development**: Work in feature-based sprints with stories and tasks
4. **Format Matters**: Data must be stored in a format suitable for future analysis

## Scope

### In Scope
- ✅ Collecting temperature readings from Philips Hue sensors
- ✅ Collecting temperature readings from Google Nest devices
- ✅ Storing data in appropriate format (CSV, JSON, database TBD)
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
| **Google Nest** | Thermostats | High | Google Nest API / SDM API |

## Data Requirements

### Minimum Data Points Per Reading
- **Timestamp**: ISO 8601 format with timezone
- **Source**: Device identifier (unique)
- **Temperature**: Celsius (standardized)
- **Location**: Room/zone identifier
- **Device Type**: Hue sensor vs Nest thermostat

### Optional Metadata
- Humidity (if available)
- Battery level (for sensors)
- Signal strength/connectivity status
- Raw API response (for debugging)

## Technical Constraints

### Development Approach
- Use tools from available tech stack (Python preferred for rapid development)
- File-based storage acceptable initially (SQLite/CSV)
- Can upgrade to proper database if needed
- Local execution on Mac Studio (no cloud deployment required)

### Performance Requirements
- Collection frequency: Every 5-15 minutes (TBD based on API limits)
- Data retention: Indefinite (storage not a constraint)
- API rate limits must be respected
- Graceful degradation if devices offline

## Sprint Structure

### Sprint Definition
- **Duration**: Flexible (1-2 weeks typical)
- **Goal**: Deliver one complete feature
- **Components**: Multiple stories, each with tasks
- **Output**: Working, committed code + documentation
- **Branch**: Named `sprint-N-name` created from `main`
- **Documentation**: `specification.md` and `plan.md` in `sprints/sprint-N-name/`

### Sprint Workflow
1. **Planning**: Create sprint branch, write specification.md and plan.md
2. **Development**: Implement stories/tasks on sprint branch
3. **Validation**: Verify deliverables meet acceptance criteria
4. **Merge**: Merge sprint branch to `main` when complete
5. **Retrospective**: Update plan.md with outcomes and learnings

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
│   └── tech-stack.md
├── sprints/
│   ├── sprint-0-foundation/
│   │   ├── specification.md
│   │   └── plan.md
│   ├── sprint-1-hue/
│   │   ├── specification.md
│   │   └── plan.md
│   ├── sprint-2-nest/
│   │   ├── specification.md
│   │   └── plan.md
│   ├── sprint-3-automation/
│   │   ├── specification.md
│   │   └── plan.md
│   └── sprint-4-quality/
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
- **specification.md**: Detailed requirements, acceptance criteria, and technical design
- **plan.md**: Task breakdown, time estimates, dependencies, and progress tracking

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
   - Implement retry logic for API failures
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
- Log errors for debugging

### Maintainability
- Quick and dirty acceptable
- Code should be understandable in 6 months
- Minimal dependencies

---

**Next Steps**: Create Sprint 1 planning document and begin implementation.

