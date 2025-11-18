# Phase 0: Research - Sprint 0 Project Foundation

**Feature**: 001-project-foundation  
**Created**: 2025-11-18  
**Purpose**: Resolve technical unknowns and establish best practices for project foundation

## Research Tasks

All technical decisions for this sprint have been pre-determined by the project constitution (docs/project-outliner.md) and session clarifications (2025-11-18). No additional research required.

## Technology Choices

### Python Version
**Decision**: Python 3.11+  
**Rationale**: Modern Python version with good type hinting support, available on macOS, stable and widely supported.  
**Alternatives Considered**: Python 3.9+ would work but 3.11 offers performance improvements and better error messages.

### Configuration Format
**Decision**: YAML  
**Rationale**: Human-readable, supports comments, widely used for configuration, good Python library support (PyYAML).  
**Alternatives Considered**: 
- JSON: Less readable, no comments
- TOML: Good but less familiar
- INI: Too limited for nested structures

### Database Choice
**Decision**: SQLite (from constitution)  
**Rationale**: Serverless, zero configuration, perfect for local single-user application, excellent for time-series data, built into Python stdlib.  
**Alternatives Considered**: 
- CSV files: Poor for queries, no schema enforcement
- PostgreSQL: Overkill for local-only tool
- JSON files: Inefficient for queries

### Virtual Environment
**Decision**: Python venv (stdlib)  
**Rationale**: Built into Python, no additional tools needed, simple and reliable.  
**Alternatives Considered**:
- conda: Too heavy for this simple project
- poetry: Additional dependency, unnecessary complexity
- pipenv: Good but adds dependency

### Dependency Management
**Decision**: requirements.txt  
**Rationale**: Simple, standard, works with pip, version-pinnable, easy to understand.  
**Alternatives Considered**: 
- Pipfile: Requires pipenv
- pyproject.toml: More complex than needed for this project

## Best Practices

### Directory Structure
**Practice**: Separate source, config, data, docs, tests at root level  
**Source**: Python Packaging Guide, Django project structure  
**Application**: Clear separation of concerns, easy to navigate, standard Python layout

### Configuration Management
**Practice**: Separate config (settings) from secrets (credentials)  
**Source**: 12-factor app methodology  
**Application**: 
- `config.yaml`: Non-sensitive settings (intervals, paths)
- `secrets.yaml`: API keys, tokens (gitignored)
- `secrets.yaml.example`: Template without real secrets

### Database Schema Design
**Practice**: Use explicit schema with constraints, indexes on query fields  
**Source**: SQLite documentation, time-series database patterns  
**Application**:
- Composite primary key or auto-increment ID
- Index on timestamp for time-range queries
- Index on device_id for per-device queries
- NOT NULL constraints on required fields
- CHECK constraints for temperature ranges

### Error Handling
**Practice**: Fail fast on configuration errors, graceful degradation on runtime errors  
**Source**: Python error handling best practices  
**Application**:
- Validate config at startup, exit with clear error if invalid
- Handle missing files with helpful messages
- Use logging for runtime issues

### Security
**Practice**: Never commit secrets, use .gitignore, no hardcoded credentials  
**Source**: OWASP security guidelines  
**Application**:
- Add `config/secrets.yaml` to .gitignore
- Add `data/` directory to .gitignore
- Provide example templates only
- Log warnings but never log secret values

## Integration Patterns

### Configuration Loading Pattern
```
1. Application starts
2. Load config.yaml (required)
3. Load secrets.yaml (required for API collectors, optional for foundation)
4. Validate all required fields present
5. Validate types and value ranges
6. Make config available to application
```

### Database Initialization Pattern
```
1. Check if database file exists
2. If not exists, create with schema
3. If exists, verify schema version (future: migrations)
4. Create connection pool/manager
5. Return ready-to-use database handle
```

### Error Reporting Pattern
```
1. Use Python logging module (stdlib)
2. Log levels: DEBUG (development), INFO (normal), WARNING (recoverable), ERROR (failures), CRITICAL (fatal)
3. Log to console during development
4. Future: Log to file with rotation
```

## Dependencies Justification

### PyYAML
**Purpose**: Parse YAML configuration files  
**Why Needed**: Standard library has no YAML support  
**Alternatives**: 
- ruamel.yaml: More features but heavier
- JSON with comments hack: Non-standard
**Version**: Latest stable (6.0+)

### SQLite3 (stdlib)
**Purpose**: Database operations  
**Why Needed**: Data persistence and querying  
**Already Included**: Part of Python standard library

### typing (stdlib)
**Purpose**: Type hints for better code clarity  
**Why Needed**: Improves maintainability and IDE support  
**Already Included**: Part of Python standard library

### pathlib (stdlib)
**Purpose**: Cross-platform path handling  
**Why Needed**: Reliable file system operations  
**Already Included**: Part of Python standard library

## Risks and Mitigations

### Risk: Python version mismatch
**Impact**: Code may not run on different machines
**Mitigation**: Document Python 3.11+ requirement in README, check version at startup

### Risk: Missing system dependencies
**Impact**: Virtual environment creation fails  
**Mitigation**: Document macOS/Python prerequisites, provide clear error messages

### Risk: Database file corruption
**Impact**: Data loss  
**Mitigation**: SQLite is robust, future: add backup strategy (Sprint 5)

### Risk: Config file syntax errors
**Impact**: Application fails to start  
**Mitigation**: Validate YAML syntax, provide clear error messages with line numbers

### Risk: Disk space exhaustion
**Impact**: Database writes fail  
**Mitigation**: Acceptable for MVP, future: monitor disk space (Sprint 5)

## Phase 0 Completion

✅ **All research tasks completed**  
✅ **No NEEDS CLARIFICATION markers remain**  
✅ **Technology choices documented with rationale**  
✅ **Best practices identified for each area**  
✅ **Integration patterns defined**  
✅ **Dependencies justified**  
✅ **Risks identified with mitigations**

**Status**: Ready to proceed to Phase 1 (Design & Contracts)
