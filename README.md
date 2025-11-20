# Home Temperature Monitoring

## Overview
A Python-based system for collecting and storing temperature readings from multiple IoT devices. Uses SQLite for local storage and YAML for configuration.

## Features

### ✅ Philips Hue Temperature Collection (Sprint 1)
- Automatic Hue Bridge discovery and authentication
- Temperature data collection from Hue motion sensors
- 5-minute collection intervals with retry logic
- SQLite database storage with duplicate detection
- Battery level and signal strength monitoring

**Status**: Complete  
**Documentation**: [Hue Integration Quickstart](specs/002-hue-integration/quickstart.md)

### 🔜 Upcoming Features
- Amazon Alexa Air Quality Monitor Integration (Sprint 2)
- Google Nest Integration (Sprint 3)
- Weather API Integration (Sprint 4)
- Automated Collection Scheduling (Sprint 4)
- Data Analysis & Visualization (Future)

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Authenticate with Hue Bridge
```bash
python source/collectors/hue_auth.py
```

### Collect Temperature Data
```bash
# Single collection
python source/collectors/hue_collector.py --collect-once

# Continuous collection (every 5 minutes)
python source/collectors/hue_collector.py --continuous
```

### Query Data
```bash
sqlite3 data/readings.db "SELECT * FROM readings WHERE device_type='hue_sensor' LIMIT 10;"
```

## Project Structure
```
source/
├── collectors/           # Data collection modules
│   ├── hue_auth.py      # Hue Bridge authentication
│   └── hue_collector.py # Hue temperature collection
├── storage/             # Database management
│   ├── manager.py       # Database operations
│   └── schema.py        # Schema definitions
├── config/              # Configuration handling
│   ├── loader.py        # Config loader
│   └── validator.py     # Config validation
└── utils/               # Utility modules
    └── logging.py       # Logging utilities

config/
├── config.yaml          # Application configuration
└── secrets.yaml         # API keys and credentials (gitignored)

data/
└── readings.db          # SQLite temperature database

specs/
├── 001-project-foundation/  # Initial setup documentation
└── 002-hue-integration/     # Hue feature specification
```

## Documentation
- [Project Constitution](docs/project-outliner.md) - Development principles and constraints
- [Hue Integration Guide](specs/002-hue-integration/quickstart.md) - Complete Hue setup walkthrough
- [Feature Specifications](specs/) - Detailed feature documentation

## Usage
- Activate virtual environment
- Run scripts in source/
- Data stored in data/readings.db
- Configuration in config/config.yaml
