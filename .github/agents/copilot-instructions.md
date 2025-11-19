# HomeTemperatureMonitoring Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-18

## Active Technologies
- SQLite database (as per constitution) (002-hue-integration)
- Python 3.11+ + sqlite3 (stdlib), phue (Hue Bridge API), PyYAML (config), logging (stdlib with RotatingFileHandler) (003-system-reliability)
- SQLite database (data/readings.db) with WAL mode enabled (003-system-reliability)

- Python 3.11+ + PyYAML (config), SQLite3 (stdlib, database), typing (stdlib, type hints) (001-project-foundation)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 003-system-reliability: Added Python 3.11+ + sqlite3 (stdlib), phue (Hue Bridge API), PyYAML (config), logging (stdlib with RotatingFileHandler)
- 002-hue-integration: Added Python 3.11+

- 001-project-foundation: Added Python 3.11+ + PyYAML (config), SQLite3 (stdlib, database), typing (stdlib, type hints)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
