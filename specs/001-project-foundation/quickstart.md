# Quickstart Guide: Sprint 0 - Project Foundation

**Last Updated**: 2025-11-18  
**Prerequisites**: macOS, Python 3.11+, git

## Overview

This quickstart guide walks you through setting up the Home Temperature Monitoring project development environment. After completing these steps, you'll have a working project structure, configured virtual environment, and initialized database ready for data collection implementation.

**Time Required**: ~10 minutes

---

## Step 1: Clone Repository

```bash
# Clone the repository (if not already done)
cd ~/Dev  # or your preferred projects directory
git clone <repository-url> HomeTemperatureMonitoring
cd HomeTemperatureMonitoring

# Verify you're on the project foundation branch
git checkout 001-project-foundation
```

---

## Step 2: Verify Python Version

```bash
# Check Python version (must be 3.11 or higher)
python3 --version

# If version is too old, install Python 3.11+ via Homebrew
# brew install python@3.11
```

**Expected Output**: `Python 3.11.x` or higher

---

## Step 3: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv) prefix
# Verify virtual environment is active
which python
# Should show: /path/to/HomeTemperatureMonitoring/venv/bin/python
```

---

## Step 4: Install Dependencies

```bash
# Install required packages
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list
# Should include: PyYAML and other dependencies
```

---

## Step 5: Configure Application

```bash
# Copy configuration templates
cp specs/001-project-foundation/contracts/config.yaml config/
cp specs/001-project-foundation/contracts/secrets.yaml.example config/secrets.yaml

# Edit configuration (optional for foundation sprint)
# nano config/config.yaml

# Edit secrets (optional for foundation sprint, required for data collection sprints)
# nano config/secrets.yaml
```

**Note**: For Sprint 0, you can leave secrets.yaml with placeholder values. Real credentials will be needed in Sprint 1 (Hue) and Sprint 2 (Nest).

---

## Step 6: Initialize Database

```bash
# Create data directory
mkdir -p data

# Initialize database with schema
sqlite3 data/readings.db < specs/001-project-foundation/contracts/database-schema.sql

# Verify database was created
ls -lh data/readings.db

# Verify schema
sqlite3 data/readings.db ".schema readings"
```

**Expected Output**: Should display the `readings` table schema with all columns and indexes.

---

## Step 7: Verify Setup

```bash
# Run verification script (to be created in implementation)
# python source/verify_setup.py

# For now, verify manually:
# 1. Virtual environment active? (venv) in prompt
# 2. Dependencies installed? pip list shows PyYAML
# 3. Config files exist? ls config/
# 4. Database exists? ls data/readings.db
# 5. Database schema valid? sqlite3 data/readings.db ".tables"
```

---

## Step 8: Run Tests (Manual Verification)

### Test Configuration Loading
```bash
# Test that configuration can be loaded (to be implemented)
# python -c "from source.config.loader import load_config; print(load_config())"
```

### Test Database Connection
```bash
# Verify database is accessible
sqlite3 data/readings.db "SELECT COUNT(*) FROM readings;"
# Expected: 0 (empty table)

# Test inserting a sample reading
sqlite3 data/readings.db <<EOF
INSERT INTO readings (timestamp, device_id, temperature_celsius, location, device_type)
VALUES (datetime('now'), 'test:device001', 21.5, 'test_location', 'hue_sensor');
SELECT * FROM readings;
EOF

# Clean up test data
sqlite3 data/readings.db "DELETE FROM readings WHERE device_id LIKE 'test:%';"
```

---

## Common Issues & Solutions

### Issue: `python3: command not found`
**Solution**: Install Python 3.11+ via Homebrew: `brew install python@3.11`

### Issue: `pip: command not found` (in virtual environment)
**Solution**: Virtual environment activation failed. Run `source venv/bin/activate` again.

### Issue: `ModuleNotFoundError: No module named 'yaml'`
**Solution**: Dependencies not installed. Run `pip install -r requirements.txt`

### Issue: Database file permissions error
**Solution**: Ensure `data/` directory exists and is writable: `mkdir -p data && chmod 755 data`

### Issue: YAML syntax error when loading config
**Solution**: Validate YAML syntax online or with `python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"`

---

## Next Steps

After completing this quickstart:

1. **Read Documentation**: Review `docs/project-outliner.md` for project overview
2. **Review Data Model**: Check `specs/001-project-foundation/data-model.md`
3. **Examine Schema**: Study `specs/001-project-foundation/contracts/database-schema.sql`
4. **Proceed to Sprint 1**: Begin Philips Hue integration when ready

---

## Project Structure Reference

```
HomeTemperatureMonitoring/
├── venv/                    # Virtual environment (created in Step 3)
├── source/                  # Application code (to be implemented)
├── config/                  # Configuration files (created in Step 5)
│   ├── config.yaml
│   └── secrets.yaml        # Gitignored
├── data/                    # Data storage (created in Step 6)
│   └── readings.db         # SQLite database
├── specs/                   # Feature specifications
│   └── 001-project-foundation/
├── docs/                    # Documentation
├── tests/                   # Test files (to be implemented)
├── requirements.txt         # Python dependencies
├── .gitignore              # Git exclusions
└── README.md               # Project overview
```

---

## Useful Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Deactivate virtual environment
deactivate

# Update dependencies
pip install --upgrade -r requirements.txt

# Check database size
du -h data/readings.db

# Query recent readings
sqlite3 data/readings.db "SELECT * FROM readings ORDER BY timestamp DESC LIMIT 10;"

# Count readings by device
sqlite3 data/readings.db "SELECT device_id, COUNT(*) FROM readings GROUP BY device_id;"

# Export data to CSV (for analysis)
sqlite3 -header -csv data/readings.db "SELECT * FROM readings;" > export.csv
```

---

## Support

If you encounter issues not covered here:
1. Check `specs/001-project-foundation/plan.md` for detailed implementation notes
2. Review project constitution: `docs/project-outliner.md`
3. Consult Python/SQLite documentation
4. Check git history for recent changes

---

**Quickstart Complete!** ✅

Your development environment is now ready. The foundation is in place for implementing data collection in subsequent sprints.
