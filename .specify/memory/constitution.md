<!--
Sync Impact Report
Version change: 2.0.1 → 2.0.2 (PATCH: Added report naming convention to File Structure section)
Modified sections:
  - Added `docs/reports/` subdirectory with naming format specification
  - Format: `YYYY-MM-DD-spec-NNN-phase-N-description.md`
  - Example provided for clarity
  - No principle changes, documentation clarification only
Templates requiring updates: ✅ No template changes required
Follow-up TODOs: None
-->

# Home Temperature Monitoring Constitution

## ⚠️ Critical Reminders for AI Agents

**READ THIS FIRST** before any work in this repository:

1. **ALWAYS ACTIVATE PYTHON VENV FIRST**: `source venv/bin/activate` before any Python commands
   - Verify: `which python` should show `/Users/peternicholls/Dev/HomeTemperatureMonitoring/venv/bin/python`
   - Running without venv wastes time with dependency errors and test failures

2. **VERIFY TECH STACK OPTIONS**: Review `docs/tech-stack.md` before choosing implementation language
   - Available: Python, Swift, C/C++, Node.js
   - Default: Python 3.14.0+ (activated venv required)
   - Performance: Profile before switching to Swift/C++
   - Consider: Swift/C++ for performance-critical paths (profile first)

3. **TEST-DRIVEN DEVELOPMENT**: Write tests before implementation (not 'quick and dirty' anymore)
   - Minimum 80% coverage for new code
   - Framework: pytest with async support (anyio) and comprehensive mocking
   - Framework: pytest with async support and mocking

4. **RESEARCH COMPLEX FEATURES**: Document research in research.md before coding
   - Required for: OAuth flows, GraphQL APIs, new integrations
   - Include: API investigation, experiments, failed attempts, successful patterns
   - See: Sprint 004 (Amazon AQM) as example
   - Capture: API investigation, experiments, failed attempts, successful patterns, and any other detailed work

5. **WRITE IMPLEMENTATION REPORTS**: After completing any phase, create report in `docs/reports/`
   - Follow: `.specify/templates/commands/report-writing-process.md` (20-step process)
   - Template: `.specify/templates/report-template.md`
   - Extract lessons learned to: `.specify/memory/lessons-learned.md` (MANDATORY)
   - Review existing lessons before starting new work

6. **CHECK CONSTITUTION**: Consult this document and `docs/project-outliner.md` before starting work
   - Verify compliance with principles and constraints
   - Follow sprint structure and Definition of Done

## Core Principles

### I. Test-Driven Development
Unit tests MUST guide implementation. Write tests before code, achieve minimum 80% coverage for new features. The project evolved from "quick and dirty" to TDD after Sprint 4 complexity demonstrated the value of comprehensive testing.  
Rationale: Complex integrations (OAuth, async APIs, GraphQL) require testing to ensure reliability. Tests prevent regressions and document expected behavior.

### II. Research-Driven Development
Complex features MUST include research documentation (research.md) with API investigation, experimentation logs, and iteration notes. Sprint 4 (Amazon AQM) demonstrated the necessity of documented research cycles.  
Rationale: Complex APIs require exploration before implementation. Research logs capture decisions, failed attempts, and successful patterns for future reference.

### III. Data Collection Focus
The project MUST focus on collecting and storing data correctly, not analyzing it. All code and tasks should serve the goal of reliable, validated data acquisition.  
Rationale: Analysis is explicitly out of scope; future projects will handle it.

### IV. Sprint-Based Development
Work is organized in feature-based sprints (numbered 001, 002, 003...), each with comprehensive specifications. Sprints MUST produce working code, tests, and documentation.  
Rationale: Enables incremental delivery and clear progress tracking with Pull Request reviews.

### V. Format Matters
Data MUST be stored in SQLite database in analysis-ready format with proper schema, timestamps, and metadata.  
Rationale: Ensures collected data is usable for statistical analysis and advocacy. SQLite chosen over CSV for query efficiency.

### VI. Tech Stack Diversity
Consider full tech stack options (Python, Swift, C/C++, Node.js) for each task. Python is default, but Swift/C++ SHOULD be evaluated for performance-critical paths. See `docs/tech-stack.md` for guidance.  
Rationale: Mac Studio M2 Ultra provides 128GB RAM and 60-core GPU (Metal). Leverage hardware capabilities appropriately.

### VII. Python Virtual Environment Mandatory
All Python code MUST run inside activated virtual environment (`source venv/bin/activate`). AI agents frequently forget this step.  
Rationale: Running outside venv causes dependency errors, test failures, and wastes tokens/time with troubleshooting.

### VIII. Knowledge Capture and Retention
All implementation phases MUST produce detailed reports documenting test results, technical decisions, and lessons learned. Lessons learned MUST be extracted to central knowledge base (`.specify/memory/lessons-learned.md`) to prevent repeating past mistakes.  
Rationale: Across Sprint 005 phases, recurring patterns emerged (TDD value, error classification, integration test priority). Capturing these systematically enables continuous improvement and informed decision-making on future work.

## Scope

### In Scope
- ✅ Collect temperature readings from Philips Hue sensors (IMPLEMENTED - Sprint 1)
- ✅ Collect air quality and temperature readings from Amazon Alexa Air Quality Monitor (IMPLEMENTED - Sprint 4)
- ⏳ Collect temperature readings from Google Nest devices (PLANNED - Sprint 6)
- ⏳ Collect outside temperature from aggregate weather API services (PLANNED)
- ✅ Store data in SQLite database for efficient querying and analysis (IMPLEMENTED)
- ✅ Timestamping and metadata for each reading (IMPLEMENTED)
- ⏳ Comprehensive error handling and retry logic (IN PROGRESS - Sprint 5)
- ⏳ Automated scheduled collection (PARTIAL - collector code ready, scheduling pending Sprint 7)

### Out of Scope
- Data analysis and visualization (future project)
- Real-time alerting or monitoring
- Historical data migration
- User interface or dashboard (basic Flask web interface exists for testing only)
- Complex data transformations

### Completed Implementations
- **Sprint 0 (001-project-foundation)**: Project structure, config management, SQLite schema ✅
- **Sprint 1 (002-hue-integration)**: Hue Bridge authentication, sensor discovery, 18 unit tests ✅
- **Sprint 4 (004-alexa-aqm-integration)**: Amazon AQM GraphQL API, OAuth, async collectors, 15 unit tests, security audit ✅

## Data Requirements

- Timestamp: ISO 8601 format with timezone
- Device ID: Composite format `source_type:device_id` (e.g., `hue:sensor_abc123`)
- Temperature: Celsius (standardized, metric only)
- Location: Room/zone identifier (or "outside" for weather data)
- Device Type: Hue sensor, Alexa air quality monitor, Nest thermostat, or weather API
- Indoor temp range: 0°C to 40°C (flag anomalies)
- Outside temp range: -40°C to 50°C
- Air quality metrics: PM2.5, PM10, VOC (volatile organic compounds), CO2 equivalent (ppm)
- Air quality index: Standardized AQI (0-500 scale) or device-specific rating
- Duplicate timestamp detection per device
- Required field presence validation
- Weather conditions index: standardized categorical values (see project docs)
- Optional metadata: humidity, battery, signal, thermostat mode/state, day/night indicator, air quality rating/category, raw API response

## Technical Constraints

### Development Environment (CRITICAL)
- **Python Virtual Environment**: MUST activate venv before any Python operations: `source venv/bin/activate`
- Verify activation: `which python` should show `/Users/peternicholls/Dev/HomeTemperatureMonitoring/venv/bin/python`
- All dependencies installed via pip within venv: `pip install -r requirements.txt`
- AI agents frequently forget venv activation - always check first to avoid wasting tokens

### Tech Stack Selection
- **Default**: Python 3.14.0+ for data collection, API integration, rapid development
- **Performance-Critical**: Evaluate Swift or C/C++ for bottlenecks (profile first)
- **Reference**: Full options documented in `docs/tech-stack.md`
- **Available**: Python, Swift, C/C++, Node.js, Zsh/Bash (via Makefile)
- **Hardware**: Mac Studio M2 Ultra (128GB RAM, 60-core GPU via Metal)
- **Frameworks**: Consider Apple frameworks (Core ML, Metal, Accelerate) for on-device ML and GPU acceleration

### Storage & Execution
- SQLite database for structured storage and efficient time-series queries
- Database file: `data/temperature_readings.db`
- Local execution only (no cloud deployment)
- Collection frequency: Every 5 minutes (288 readings/day per sensor), flexible to 10-15 if rate limited
- Data retention: Indefinite
- API rate limits MUST be respected
- Graceful degradation if devices offline

## Sprint Structure

### Sprint Numbering & Branching
- Sprints numbered **001**, **002**, **003**, etc. (zero-padded, three digits)
- Branch naming: `NNN-short-name` (e.g., `001-project-foundation`, `002-hue-integration`)
- Spec directories: `specs/NNN-name/` (e.g., `specs/001-project-foundation/`)
- Default branch: `master` (stable, production-ready code)
- Feature branches created from `master`, merged via Pull Request with code review

### Sprint Documentation (Comprehensive)
Each spec folder (`specs/NNN-name/`) MUST contain:
- **spec.md**: User scenarios, functional requirements, acceptance criteria, edge cases, success criteria
- **plan.md**: Implementation plan, task breakdown, dependencies, progress tracking
- **research.md**: API research, technical investigation, experimentation log (required for complex features)
- **data-model.md**: Database schema, data structures, API contracts
- **quickstart.md**: Quick reference guide and usage instructions
- **checklists/**: Quality validation checklists (requirements, implementation, testing)
- **contracts/**: API contracts and interface definitions
- **tasks.md**: Detailed task list with status tracking

### Sprint Workflow (Test-Driven)
1. **Planning**: Create sprint branch, write spec.md and plan.md
2. **Research**: Investigate APIs, document findings in research.md (critical for complex features like OAuth, GraphQL)
3. **Test Design**: Write test cases based on acceptance criteria (TDD approach, pytest framework)
4. **Implementation**: Implement features to pass tests (iterate: test → code → refine)
5. **Validation**: Verify deliverables meet acceptance criteria, run full test suite in venv
6. **Code Review**: Self-review or automated analysis before merge
7. **Report Writing**: Create implementation report in `docs/reports/` following report-writing-process.md
8. **Lessons Extraction**: Extract lessons learned to `.specify/memory/lessons-learned.md` (mandatory)
9. **Merge**: Merge to `master` via Pull Request
10. **Retrospective**: Update plan.md with outcomes, learnings, metrics, and challenges

### Definition of Done (Enhanced)
- [ ] Unit tests written and passing (minimum 80% coverage for new code)
- [ ] Feature implemented following TDD approach (tests written first)
- [ ] All tests passing in Python venv: `pytest tests/`
- [ ] Research documented in research.md (if complex feature requiring API exploration)
- [ ] Code committed to git with descriptive messages referencing sprint/story
- [ ] Documentation updated (spec.md, plan.md, quickstart.md, README if applicable)
- [ ] **Implementation report written** following `.specify/templates/commands/report-writing-process.md`
- [ ] **Lessons learned extracted** to `.specify/memory/lessons-learned.md`
- [ ] Data collection verified working in real environment (not just mocked tests)
- [ ] No breaking changes to existing data format or API contracts
- [ ] Security review completed (credentials, secrets, API exposure, OAuth flows)

## Development Workflow

### Branch Strategy
- `master`: Stable, production-ready code (default branch)
- `NNN-short-name`: Feature branches (e.g., `001-project-foundation`, `002-hue-integration`, `005-system-reliability`)
- Feature branches created from `master`, merged via Pull Request when complete
- Each feature corresponds to a spec in `specs/NNN-name/`

**Completed Branches** (merged to master):
- `001-project-foundation` ✅
- `002-hue-integration` ✅
- `004-alexa-aqm-integration` ✅

**Active Branch**:
- `005-system-reliability` ⏳

### Commit Standards
- Descriptive messages explaining why, not just what
- Reference sprint/story/task if applicable (e.g., "feat(005): implement WAL mode for database")
- Working code only (or clearly marked WIP in branch)
- Conventional Commits format preferred: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`

### Testing Standards (Test-Driven Development)
- **Approach**: Write tests before implementation (TDD)
- **Framework**: pytest with async support and comprehensive mocking
- **Coverage**: Minimum 80% for new code, focus on critical paths
- **Current Tests**: 33 total (18 Hue + 15 Amazon AQM)
- **Mocking**: Comprehensive mocking for external APIs (avoid actual API calls in unit tests)
- **Integration Testing**: Manual validation for real API integration
- **Evaluation Framework**: Automated evaluation with test datasets (`evaluation.py`)
- **Research Documentation**: Complex features require research logs (see Sprint 4 example)
- **Iteration Cycle**: Expect multiple rounds of research → experiment → test → refine

### File Structure
- `source/`: Python source code (collectors, storage, config, utils, web)
- `specs/`: Sprint documentation (001, 002, 003, 004, 005...)
- `tests/`: Unit tests (pytest), manual test scripts
- `data/`: SQLite database, evaluation datasets
- `config/`: Configuration files (config.yaml, secrets.yaml - gitignored)
- `docs/`: Project documentation (guides, tech stack, evaluation framework)
  - `docs/reports/`: Implementation reports with naming format: `YYYY-MM-DD-spec-NNN-phase-N-description.md`
    - Example: `2024-11-31-spec-005-phase-5-log-rotation-implementation-report.md`
- `logs/`: Application logs (gitignored)
- `.specify/`: Spec Kit framework
  - `templates/`: Document templates (spec, plan, tasks, report)
  - `templates/commands/`: Process documentation (report-writing-process.md)
  - `memory/`: Central knowledge base (constitution.md, lessons-learned.md)

## Success Criteria

The project is successful when:
1. ✅ Temperature data is collected from Philips Hue sensors (ACHIEVED)
2. ✅ Air quality metrics (PM2.5, PM10, VOC, CO2e) collected from Amazon Alexa Air Quality Monitor (ACHIEVED)
3. ⏳ Temperature data collected from Google Nest thermostats (PENDING - Sprint 6)
4. ✅ Data stored in SQLite database in consistent, analysis-ready format (ACHIEVED)
5. ⏳ Collection runs automatically on schedule (PARTIAL - collector code ready, scheduling pending Sprint 7)
6. ⏳ System recovers gracefully from temporary failures (IN PROGRESS - Sprint 5)
7. ✅ Data format documented and stable (ACHIEVED)
8. ✅ Comprehensive test coverage (80%+) for all collectors (ACHIEVED - 33 tests)
9. ✅ Security audit completed for authentication flows (ACHIEVED - Sprint 4)

## API & Authentication Notes

### Philips Hue (IMPLEMENTED ✅)
- Local network access to Hue Bridge required
- Authentication: Bridge button press + API key generation
- API key stored in `secrets.yaml` (gitignored)
- Local API only (no cloud dependency)
- Implementation files: `source/collectors/hue_auth.py`, `source/collectors/hue_collector.py`
- Documentation: `docs/hue-authentication-guide.md`
- Rate limits: Generous for local polling

### Amazon Alexa Air Quality Monitor (IMPLEMENTED ✅)
- GraphQL API via Amazon Web Services (cloud-based)
- OAuth 2.0 authentication: Login with Amazon (LWA)
- Tokens stored in `secrets.yaml` with automatic refresh
- Implementation files: `source/collectors/amazon_auth.py`, `source/collectors/amazon_collector.py`
- Async/await pattern for efficient data collection
- Documentation: `docs/Amazon-Alexa-Air-Quality-Monitoring/`
- Complex integration requiring extensive research (see `specs/004-alexa-aqm-integration/research.md`)

### Google Nest (PLANNED ⏳)
- Google Cloud project setup required
- OAuth 2.0 authentication
- Smart Device Management (SDM) API
- Rate limits: TBD based on quotas
- $5 one-time SDM API access fee required
- Implementation planned for Sprint 6

## Non-Functional Requirements

### Security
- API keys/secrets stored in gitignored `config/secrets.yaml` only
- No hardcoded credentials anywhere in codebase
- OAuth tokens with automatic refresh (Amazon AQM)
- Local network only for Hue Bridge (no external exposure)
- Security audit required for all authentication flows (completed for Sprints 1 and 4)

### Reliability
- System MUST NOT crash on API failures (graceful degradation)
- Retry policy: 3 attempts with exponential backoff (1s, 2s, 4s delays)
- After retry exhaustion, log failure and continue to next scheduled collection
- Acceptable to miss occasional readings due to temporary failures
- Comprehensive error handling for transient vs permanent failures (Sprint 5 focus)
- Database integrity checks and WAL mode for concurrent access

### Maintainability
- Test-driven development for reliability (evolved from "quick and dirty" after Sprint 4)
- Code MUST be understandable in 6 months (clear naming, documentation, type hints)
- Minimal dependencies per language ecosystem
- Research documentation required for complex features
- Tech stack alternatives considered for performance-critical code (see `docs/tech-stack.md`)

### Performance
- Profile before optimizing (measure actual bottlenecks, don't guess)
- Consider Swift/C++ for performance-critical paths (Core ML, Metal GPU acceleration)
- Leverage Mac Studio M2 Ultra capabilities (128GB RAM, 60-core GPU)
- Python default unless profiling demonstrates need for compiled languages
- Collection cycles SHOULD complete in under 30 seconds (target from Sprint 5)

### Testing
- Minimum 80% code coverage for new features
- Unit tests written before implementation (TDD)
- Comprehensive mocking for external APIs (no actual API calls in unit tests)
- Integration tests with real APIs in manual test suite
- All tests MUST run in Python virtual environment
- Automated evaluation framework for end-to-end validation

## Governance

### Constitutional Authority
- This constitution supersedes all other practices for this project
- All sprints, plans, and specs MUST verify compliance with principles and constraints
- AI agents MUST consult this constitution and `docs/project-outliner.md` before beginning work

### Amendment Process
- Amendments require:
  1. Documentation of rationale and impact
  2. Update to this constitution with version bump
  3. Sync Impact Report (HTML comment at top of file)
  4. Migration plan for affected code/docs if needed
  5. Update to `docs/project-outliner.md` to match

### Versioning Policy
- **MAJOR** (X.0.0): Backward incompatible principle removals or redefinitions (e.g., 1.2.0 → 2.0.0 for TDD replacement of "Quick and Dirty")
- **MINOR** (x.X.0): New principle/section added or materially expanded guidance
- **PATCH** (x.x.X): Clarifications, wording, typo fixes, non-semantic refinements

### Compliance Review
- Compliance review required at each sprint retrospective
- Any complexity or deviation MUST be justified in sprint documentation (research.md, plan.md)
- Template adherence verified via checklists in `specs/NNN-name/checklists/`

---

**Version**: 2.1.0 | **Ratified**: 2025-11-18 | **Last Amended**: 2025-11-21