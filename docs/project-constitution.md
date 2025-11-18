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

### Definition of Done (per Sprint)
- [ ] Feature implemented and tested
- [ ] Code committed to git
- [ ] Documentation updated
- [ ] Data collection verified working
- [ ] No breaking changes to existing data format

## Development Workflow

### Branch Strategy
- `main`: Stable, working code
- `feature/*`: Feature development branches
- `hotfix/*`: Quick fixes for broken collection

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
│   └── sprints/
│       └── sprint-001-*.md
├── src/
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

## Initial Sprint Backlog (Prioritized)

### Sprint 1: Foundation & Philips Hue Collection
- Set up project structure
- Implement Philips Hue sensor discovery and authentication
- Collect temperature data from Hue sensors
- Store data in CSV format

### Sprint 2: Google Nest Integration
- Implement Google Nest API authentication
- Collect temperature data from Nest devices
- Merge with Hue data in unified format

### Sprint 3: Automation & Scheduling
- Implement scheduled collection (cron/systemd/launchd)
- Error handling and retry logic
- Logging and monitoring

### Sprint 4: Data Quality & Refinement
- Validate data format consistency
- Add metadata enrichment
- Consider database migration if needed

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

