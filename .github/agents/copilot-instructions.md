````chatagent
# HomeTemperatureMonitoring Development Guidelines

## ⚠️ CRITICAL: PYTHON VENV MUST BE ACTIVE

**BEFORE ANY PYTHON COMMAND** (pytest, pip, python, etc.):

```bash
# Verify venv is active
which python  # Must show: /Users/peternicholls/Dev/HomeTemperatureMonitoring/venv/bin/python

# If not active, activate it:
source venv/bin/activate
```

**Why**: Running pytest without venv causes `ModuleNotFoundError` for phue, pyyaml, etc.

---

## 🚀 AGENT SESSION INITIALIZATION

**IMPORTANT**: Run this command when starting a new session:

```bash
source .specify/scripts/bash/init-agent-session.sh
```

This initialization script will:
1. ✅ Display critical constitution reminders (6 key requirements)
2. ✅ Auto-activate Python virtual environment
3. 📂 Show current feature context (branch, spec files)
4. ✔️  Check prerequisites (spec.md, plan.md, tasks.md)
5. 🛠️  Display tech stack summary
6. 📋 Report task status (completed/remaining)

**Session setup time**: 10-15 seconds (automated)

---

Auto-generated from all feature plans. Last updated: 2025-11-21

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


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
