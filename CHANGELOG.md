# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Sprint 3: Amazon AQM Database Integration
- **Amazon Air Quality Monitor Integration**
  - Cookie-based authentication via web UI at http://localhost:5001/setup
  - GraphQL device discovery for Air Quality Monitor devices
  - Phoenix State API data collection for 8 sensor readings
  - Database storage for temperature, humidity, PM2.5, VOC, CO, and IAQ score
  - Automatic schema migration for new air quality columns (co_ppm, iaq_score)
  
- **Database Enhancements**
  - Added `co_ppm REAL` column for carbon monoxide measurements
  - Added `iaq_score REAL` column for indoor air quality index (0-100)
  - Updated device_type CHECK constraint to include 'alexa_aqm'
  - Auto-migration logic for existing databases
  
- **Collection Infrastructure**
  - `AmazonAQMCollector.format_reading_for_db()` - Format API readings for database insertion
  - `AmazonAQMCollector.collect_and_store()` - Convenience method for end-to-end collection
  - `source/collectors/amazon_aqm_collector_main.py` - Production collection script
  - Three operation modes: `--discover`, `--collect-once`, `--continuous`
  - Exponential backoff retry logic (1s, 2s, 4s delays)
  - Configurable 5-minute collection intervals
  
- **Authentication Functions**
  - `validate_amazon_cookies()` - Validate cookie structure and essential cookies
  - `check_cookie_expiration()` - 24-hour expiration window checking
  - `run_amazon_login()` - Web UI integration for cookie capture
  
- **Configuration**
  - Complete `collectors.amazon_aqm` section in config.yaml
  - Device location mapping support
  - Per-sensor collection toggles
  - Retry and timeout configuration
  - Cookie storage in secrets.yaml
  
- **Documentation**
  - Amazon AQM integration section in README.md
  - Complete troubleshooting guide for common issues
  - Updated quickstart guide with database integration examples
  - Inline code documentation for all new functions

### Changed
- Updated `source/storage/schema.py` with air quality sensor fields
- Enhanced `source/storage/manager.py` with migration support
- Improved cookie domain extraction for multi-part TLDs (.amazon.co.uk)
- Config normalization in main script for compatibility

### Fixed
- Cookie domain extraction bug for non-.com Amazon domains
- Database constraint migration for alexa_aqm device type
- Configuration structure compatibility (collectors.amazon_aqm → amazon_aqm)
- Cookie validation relaxed to only require essential cookies

## [0.2.0] - Sprint 2: Amazon AQM Research & API Discovery

### Added
- Amazon Alexa API research and endpoint discovery
- GraphQL device discovery endpoint identification
- Phoenix State API for sensor data retrieval
- Working test script demonstrating API integration
- Cookie-based authentication approach
- Sensor mapping documentation (8 instance IDs to physical sensors)

### Research Outcomes
- Documented Amazon Alexa GraphQL API endpoints
- Identified Phoenix State API for real-time sensor data
- Validated cookie-based authentication (18 cookies, ~24 hour lifespan)
- Mapped sensor instance IDs: 4=humidity, 5=VOC, 6=PM2.5, 7=unknown, 8=CO, 9=IAQ
- Integration plan for Sprint 3 database integration

## [0.1.0] - Sprint 1: Philips Hue Integration

### Added
- **Philips Hue Motion Sensor Integration**
  - Hue Bridge discovery and authentication
  - Temperature and humidity data collection
  - Automatic sensor discovery
  - Database storage with SQLite
  
- **Database Infrastructure**
  - SQLite database with WAL mode
  - `readings` table schema
  - Duplicate detection (UNIQUE constraint on device_id + timestamp)
  - DatabaseManager with retry logic
  
- **Configuration System**
  - YAML-based configuration (config.yaml)
  - Secrets management (secrets.yaml, gitignored)
  - Config validation
  - Example configuration files
  
- **Web Interface**
  - Flask web UI for initial setup
  - Hue authentication flow
  - Status display
  
- **Documentation**
  - Project foundation specification
  - Hue integration guide
  - Quickstart documentation
  - Code review and evaluation reports

### Infrastructure
- Python 3.10+ project structure
- Virtual environment setup
- Requirements management
- Logging utilities
- Unit test framework

## [0.0.1] - Sprint 0: Project Foundation

### Added
- Initial project structure
- Development principles and constraints
- Technology stack selection
- Directory structure
- Git repository initialization
- README with project overview
- Specification framework

---

## Version History Summary

- **v0.0.1**: Project foundation and planning
- **v0.1.0**: Philips Hue integration with database storage
- **v0.2.0**: Amazon AQM API research and endpoint discovery
- **Unreleased (v0.3.0)**: Amazon AQM database integration (Sprint 3)

## Migration Notes

### Upgrading to v0.3.0 (Sprint 3)
1. Database will auto-migrate to add `co_ppm` and `iaq_score` columns
2. Update `config/config.yaml` with `collectors.amazon_aqm` section
3. Run web UI setup to capture Amazon cookies
4. Verify device_type constraint includes 'alexa_aqm'

### Upgrading to v0.1.0 (Sprint 1)
1. Create `config/secrets.yaml` from example template
2. Initialize database with `DatabaseManager`
3. Configure Hue Bridge IP and authenticate
4. Update `config/config.yaml` with Hue settings
