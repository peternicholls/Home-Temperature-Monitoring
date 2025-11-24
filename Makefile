.PHONY: help setup clean auth auth-ip discover collect-once continuous aqm-setup aqm-discover aqm-collect aqm-continuous aqm-test nest-discover nest-collect nest-continuous nest-test web-start web-stop db-reset db-query db-view db-stats devices-list devices-set-name devices-amend devices-amend-recursive logs logs-tail logs-clear test test-discover test-full test-24hour-setup test-24hour-stop test-24hour-verify collection-init collection-start collection-stop collection-status collection-logs collection-uninstall log-view log-errors log-stats log-json lint format health-check verify-setup evaluate

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Home Temperature Monitoring - Makefile Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Environment:$(NC)"
	@echo "  make setup          - Install dependencies and setup virtual environment"
	@echo "  make clean          - Remove all build, test, and cache artifacts"
	@echo ""
	@echo "$(GREEN)Web Server (Flask UI):$(NC)"
	@echo "  make web-start      - Start Flask server for Amazon cookie capture (http://localhost:5001/setup)"
	@echo "  make web-stop       - Stop Flask server gracefully"
	@echo ""
	@echo "$(GREEN)Authentication & Configuration:$(NC)"
	@echo "  make auth           - Authenticate with Hue Bridge (press button when prompted)"
	@echo "  make auth-ip        - Authenticate with manual Bridge IP (set HUE_IP=192.168.1.x)"
	@echo ""
	@echo "$(GREEN)Philips Hue Discovery & Collection:$(NC)"
	@echo "  make discover       - List all Hue temperature sensors"
	@echo "  make collect-once   - Collect Hue readings once and store in database"
	@echo "  make continuous     - Run continuous Hue collection (Ctrl+C to stop)"
	@echo ""
	@echo "$(GREEN)Amazon Air Quality Monitor (AQM):$(NC)"
	@echo "  make aqm-discover   - List all Amazon Air Quality Monitor devices"
	@echo "  make aqm-collect    - Collect AQM readings once and store in database"
	@echo "  make aqm-continuous - Run continuous AQM collection (5-min intervals, Ctrl+C to stop)"
	@echo "  make aqm-test       - Test AQM integration (discover + collect + verify DB)"
	@echo ""	@echo "$(GREEN)Nest Thermostat via Amazon Alexa:$(NC)"
	@echo "  make nest-discover  - List all Nest thermostats via Alexa"
	@echo "  make nest-collect   - Collect Nest readings once and store in database"
	@echo "  make nest-continuous - Run continuous Nest collection (5-min intervals, Ctrl+C to stop)"
	@echo "  make nest-test      - Test Nest integration (discover + collect + verify DB)"
	@echo ""	@echo "$(GREEN)Health Check & Setup Verification:$(NC)"
	@echo "  make health-check   - Run comprehensive health check of system"
	@echo "  make verify-setup   - Verify configuration and system setup (pre-collection check)"
	@echo ""
	@echo "$(GREEN)Evaluation & Testing:$(NC)"
	@echo "  make evaluate       - Run evaluation framework on collected data (SC-001, SC-002, SC-007)"
	@echo ""
	@echo "$(GREEN)Production Testing - 24 Hour Operation:$(NC)"
	@echo "  make test-24hour-setup   - T101: Start 24-hour continuous operation test"
	@echo "  make test-24hour-stop    - Stop running 24-hour test gracefully"
	@echo "  make test-24hour-verify  - T102-T104: Verify test results (SC-001, SC-002, SC-007)"
	@echo ""
	@echo "$(GREEN)Scheduled Collection (launchd):$(NC)"
	@echo "  make collection-init     - Initialize launchd agents (one-time setup)"
	@echo "  make collection-start    - Start scheduled collection (every 5 minutes)"
	@echo "  make collection-stop     - Stop scheduled collection"
	@echo "  make collection-status   - Show scheduled collection status"
	@echo "  make collection-logs     - View scheduled collection logs"
	@echo "  make collection-uninstall - Remove launchd agents completely"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make db-reset       - Delete and recreate empty database"
	@echo "  make db-query       - Run custom SQL query (set SQL='SELECT * FROM readings')"
	@echo "  make db-view        - View recent readings in database"
	@echo "  make db-stats       - Show database statistics (row counts, sensors, etc)"
	@echo ""
	@echo "$(GREEN)Device Registry (Phase 9):$(NC)"
	@echo "  make devices-list   - List all registered devices with names"
	@echo "  make devices-set-name - Set device name (usage: DEVICE_ID='hue:ABC' NAME='Kitchen')"
	@echo "  make devices-amend  - Amend device name (usage: DEVICE_ID='hue:ABC' NAME='Living Room')"
	@echo "  make devices-amend-recursive - Amend name + update history (DEVICE_ID + NAME)"
	@echo ""
	@echo "$(GREEN)Logs:$(NC)"
	@echo "  make logs           - Show recent log entries"
	@echo "  make logs-tail      - Follow logs in real-time (Ctrl+C to stop)"
	@echo "  make logs-clear     - Clear all log files"
	@echo ""
	@echo "$(GREEN)Structured Log Analysis:$(NC)"
	@echo "  make log-view       - View structured JSON logs with colors (jq formatted)"
	@echo "  make log-errors     - Filter and show only ERROR entries"
	@echo "  make log-stats      - Generate summary statistics from logs"
	@echo "  make log-json       - Pretty-print raw JSON logs (interactive pager)"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test           - Quick test (just collect once)"
	@echo "  make test-discover  - Test with discovery + collection"
	@echo "  make test-full      - Run full integration test (auth, discover, collect, store)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make lint           - Check Python files with pylint"
	@echo "  make format         - Format Python code with black"
	@echo ""

# Setup & Environment
setup: ## Install dependencies and setup virtual environment
	@echo "$(BLUE)Setting up environment...$(NC)"
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "$(BLUE)Installing Playwright browser binaries...$(NC)"
	. venv/bin/activate && playwright install
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo "Activate with: source venv/bin/activate"

clean: ## Remove all build, test, and cache artifacts
	@echo "$(YELLOW)Cleaning artifacts...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

# Web Server (Flask UI)
web-start: ## Start Flask server for Amazon cookie capture
	@echo "$(BLUE)Starting Flask web server...$(NC)"
	@echo "$(GREEN)Navigate to: http://localhost:5001/setup$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop the server$(NC)"
	@echo ""
	. venv/bin/activate && python source/web/app.py

web-stop: ## Stop Flask server gracefully
	@echo "$(BLUE)Stopping Flask server...$(NC)"
	@pkill -f "python source/web/app.py" 2>/dev/null || true
	@echo "$(GREEN)✓ Server stopped!$(NC)"

# Authentication & Configuration
auth: ## Authenticate with Hue Bridge (press button when prompted)
	@echo "$(BLUE)Starting Hue Bridge authentication...$(NC)"
	@echo "$(YELLOW)Press the button on your Hue Bridge when the countdown appears!$(NC)"
	@echo ""
	. venv/bin/activate && python source/collectors/hue_auth.py

auth-ip: ## Authenticate with manual Bridge IP
	@if [ -z "$(HUE_IP)" ]; then \
		echo "$(RED)Error: HUE_IP not set$(NC)"; \
		echo "Usage: make auth-ip HUE_IP=192.168.1.105"; \
		exit 1; \
	fi
	@echo "$(BLUE)Authenticating with Bridge at $(HUE_IP)...$(NC)"
	@echo "$(YELLOW)Press the button on your Hue Bridge when the countdown appears!$(NC)"
	@echo ""
	. venv/bin/activate && python source/collectors/hue_auth.py --bridge-ip $(HUE_IP)

# Discovery & Collection (Hue)
discover: ## List all Hue temperature sensors
	@echo "$(BLUE)Discovering Hue temperature sensors...$(NC)"
	. venv/bin/activate && python source/collectors/hue_collector.py --discover

collect-once: ## Collect Hue readings once and store in database
	@echo "$(BLUE)Running single Hue collection cycle...$(NC)"
	. venv/bin/activate && python source/collectors/hue_collector.py --collect-once

continuous: ## Run continuous Hue collection (Ctrl+C to stop)
	@echo "$(BLUE)Starting continuous Hue collection mode...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	. venv/bin/activate && python source/collectors/hue_collector.py --continuous

# Amazon AQM
aqm-discover: ## List all Amazon Air Quality Monitor devices
	@echo "$(BLUE)Discovering Amazon AQM devices...$(NC)"
	. venv/bin/activate && python source/collectors/amazon_aqm_collector_main.py --discover

aqm-collect: ## Collect AQM readings once and store in database
	@echo "$(BLUE)Running single AQM collection cycle...$(NC)"
	. venv/bin/activate && python source/collectors/amazon_aqm_collector_main.py --collect-once

aqm-continuous: ## Run continuous AQM collection (5-min intervals)
	@echo "$(BLUE)Starting continuous AQM collection mode (5-minute intervals)...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	. venv/bin/activate && python source/collectors/amazon_aqm_collector_main.py --continuous

aqm-test: ## Test AQM integration (discover + collect + verify DB)
	@echo "$(BLUE)Running Amazon AQM integration test...$(NC)"
	@echo ""
	@echo "$(BLUE)1. Discovering AQM devices...$(NC)"
	@. venv/bin/activate && python source/collectors/amazon_aqm_collector_main.py --discover
	@echo ""
	@echo "$(BLUE)2. Collecting readings...$(NC)"
	@. venv/bin/activate && python source/collectors/amazon_aqm_collector_main.py --collect-once
	@echo ""
	@echo "$(BLUE)3. Verifying database...$(NC)"
	@. venv/bin/activate && python3 -c "import sqlite3; conn = sqlite3.connect('data/readings.db'); cursor = conn.execute(\"SELECT COUNT(*) FROM readings WHERE device_type='alexa_aqm'\"); count = cursor.fetchone()[0]; cursor2 = conn.execute(\"SELECT device_id, temperature_celsius, humidity_percent, pm25_ugm3, voc_ppb, co_ppm, iaq_score FROM readings WHERE device_type='alexa_aqm' ORDER BY timestamp DESC LIMIT 1\"); latest = cursor2.fetchone(); print(f'Total AQM readings in database: {count}'); print(f'\033[0;32m✓ Test passed! Data was stored successfully.\033[0m' if count > 0 else '\033[0;31m✗ Test failed! No data in database.\033[0m'); print(f'Latest reading: {latest}' if latest else 'No readings found'); conn.close()"

# Nest Thermostat via Amazon
nest-discover: ## List all Nest thermostats via Alexa
	@echo "$(BLUE)Discovering Nest thermostats...$(NC)"
	. venv/bin/activate && python source/collectors/nest_via_amazon_collector_main.py --discover

nest-collect: ## Collect Nest readings once and store in database
	@echo "$(BLUE)Running single Nest collection cycle...$(NC)"
	. venv/bin/activate && python source/collectors/nest_via_amazon_collector_main.py --collect-once

nest-continuous: ## Run continuous Nest collection (5-minute intervals)
	@echo "$(BLUE)Starting continuous Nest collection mode (5-minute intervals)...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	. venv/bin/activate && python source/collectors/nest_via_amazon_collector_main.py --continuous

nest-test: ## Test Nest integration (discover + collect + verify DB)
	@echo "$(BLUE)Running Nest integration test...$(NC)"
	@echo ""
	@echo "$(BLUE)1. Discovering Nest thermostats...$(NC)"
	@. venv/bin/activate && python source/collectors/nest_via_amazon_collector_main.py --discover
	@echo ""
	@echo "$(BLUE)2. Collecting readings...$(NC)"
	@. venv/bin/activate && python source/collectors/nest_via_amazon_collector_main.py --collect-once
	@echo ""
	@echo "$(BLUE)3. Verifying database...$(NC)"
	@. venv/bin/activate && python3 -c "import sqlite3; conn = sqlite3.connect('data/readings.db'); cursor = conn.execute(\"SELECT COUNT(*) FROM readings WHERE device_type='nest_thermostat'\"); count = cursor.fetchone()[0]; cursor2 = conn.execute(\"SELECT device_id, location, temperature_celsius, thermostat_mode, timestamp FROM readings WHERE device_type='nest_thermostat' ORDER BY timestamp DESC LIMIT 1\"); latest = cursor2.fetchone(); print(f'Total Nest readings in database: {count}'); print(f'\033[0;32m✓ Test passed! Data was stored successfully.\033[0m' if count > 0 else '\033[0;31m✗ Test failed! No data in database.\033[0m'); print(f'Latest reading: {latest}' if latest else 'No readings found'); conn.close()"


# Database operations
db-reset: ## Delete and recreate empty database
	@echo "$(RED)WARNING: This will delete all collected readings!$(NC)"
	@read -p "Are you sure? (y/N) " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -f data/readings.db; \
		echo "$(GREEN)✓ Database reset. Will be recreated on next collection.$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled.$(NC)"; \
	fi

db-query: ## Run custom SQL query (usage: make db-query SQL="SELECT * FROM readings LIMIT 5")
	@if [ -z "$(SQL)" ]; then \
		echo "$(RED)Error: SQL not set$(NC)"; \
		echo "Usage: make db-query SQL=\"SELECT * FROM readings LIMIT 5\""; \
		exit 1; \
	fi
	. venv/bin/activate && python3 -c "import sqlite3; conn = sqlite3.connect('data/readings.db'); cursor = conn.execute('$(SQL)'); [print(dict(zip([c[0] for c in cursor.description], row))) for row in cursor.fetchall()]; conn.close()"

db-view: ## View recent readings in database
	@echo "$(BLUE)Recent readings in database:$(NC)"
	. venv/bin/activate && python3 -c "import sqlite3; conn = sqlite3.connect('data/readings.db'); cursor = conn.execute('SELECT timestamp, name, location, device_type, thermostat_mode, temperature_celsius, humidity_percent, pm25_ugm3, voc_ppb, co_ppm, iaq_score FROM readings ORDER BY timestamp DESC LIMIT 20'); print(f\"{'Timestamp':<20} {'Name':<25} {'Location':<15} {'Type':<15} {'Mode':<10} {'Temp':<8} {'Hum%':<8} {'PM2.5':<8} {'VOC':<8} {'CO':<8} {'IAQ':<8}\"); print('-' * 150); [print(f\"{ts[:19]:<20} {n if n else '-':<25} {loc if loc else '-':<15} {dt:<15} {m if m else '-':<10} {t:<8.2f} {h if h else '-':<8} {p if p else '-':<8} {v if v else '-':<8} {c if c else '-':<8} {i if i else '-':<8}\") for ts, n, loc, dt, m, t, h, p, v, c, i in cursor.fetchall()]; conn.close()"

db-stats: ## Show database statistics
	@echo "$(BLUE)Database Statistics:$(NC)"
	. venv/bin/activate && python3 -c "import sqlite3; conn = sqlite3.connect('data/readings.db'); cursor = conn.execute('SELECT COUNT(*) FROM readings'); print(f'Total readings: {cursor.fetchone()[0]}\\n'); cursor = conn.execute('SELECT device_type, COUNT(*) FROM readings GROUP BY device_type'); print('Readings by device type:'); [print(f'  {dt}: {c}') for dt, c in cursor.fetchall()]; print(); cursor = conn.execute('SELECT device_id, location, device_type, COUNT(*) as count, MIN(temperature_celsius) as min_temp, MAX(temperature_celsius) as max_temp, AVG(temperature_celsius) as avg_temp FROM readings GROUP BY device_id, location, device_type ORDER BY device_type, location'); print(f\"{'Device ID':<45} {'Location':<15} {'Type':<12} {'Count':<8} {'Min°C':<8} {'Max°C':<8} {'Avg°C':<8}\"); print('-' * 110); [print(f\"{d:<45} {loc if loc else '-':<15} {dt:<12} {c:<8} {mi:<8.1f} {ma:<8.1f} {a:<8.1f}\") for d, loc, dt, c, mi, ma, a in cursor.fetchall()]; conn.close()"

# Device Registry (Phase 9)
devices-list: ## List all registered devices with names
	@echo "$(BLUE)Device Registry:$(NC)"
	@. venv/bin/activate && python source/storage/device_manager.py --list-devices

devices-set-name: ## Set device name (usage: make devices-set-name DEVICE_ID="hue:ABC123" NAME="Kitchen Sensor")
	@if [ -z "$(DEVICE_ID)" ] || [ -z "$(NAME)" ]; then \
		echo "$(RED)Error: DEVICE_ID and NAME required$(NC)"; \
		echo "Usage: make devices-set-name DEVICE_ID=\"hue:00:17:88:01:02:3a:bc:de-02-0402\" NAME=\"Kitchen Sensor\""; \
		exit 1; \
	fi
	@echo "$(BLUE)Setting device name...$(NC)"
	@. venv/bin/activate && python source/storage/device_manager.py --set-name "$(DEVICE_ID)" "$(NAME)"

devices-amend: ## Amend device name (registry only)
	@if [ -z "$(DEVICE_ID)" ] || [ -z "$(NAME)" ]; then \
		echo "$(RED)Error: DEVICE_ID and NAME required$(NC)"; \
		echo "Usage: make devices-amend DEVICE_ID=\"hue:00:17:88:01:02:3a:bc:de-02-0402\" NAME=\"Living Room Sensor\""; \
		exit 1; \
	fi
	@echo "$(BLUE)Amending device name (registry only)...$(NC)"
	@. venv/bin/activate && python source/storage/device_manager.py --amend-name "$(DEVICE_ID)" "$(NAME)"

devices-amend-recursive: ## Amend device name and update all historical readings
	@if [ -z "$(DEVICE_ID)" ] || [ -z "$(NAME)" ]; then \
		echo "$(RED)Error: DEVICE_ID and NAME required$(NC)"; \
		echo "Usage: make devices-amend-recursive DEVICE_ID=\"hue:00:17:88:01:02:3a:bc:de-02-0402\" NAME=\"Utility Room\""; \
		echo "$(YELLOW)WARNING: This will update ALL historical readings for this device!$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)WARNING: This will update ALL historical readings for device $(DEVICE_ID)$(NC)"
	@read -p "Are you sure? (y/N) " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "$(BLUE)Amending device name and updating history...$(NC)"; \
		. venv/bin/activate && python source/storage/device_manager.py --amend-name "$(DEVICE_ID)" "$(NAME)" --recursive; \
	else \
		echo "$(YELLOW)Cancelled.$(NC)"; \
	fi


# Logs
logs: ## Show recent log entries
	@echo "$(BLUE)Recent log entries:$(NC)"
	@tail -50 logs/collection.log 2>/dev/null || echo "$(YELLOW)No logs yet$(NC)"

logs-tail: ## Follow logs in real-time (Ctrl+C to stop)
	@echo "$(BLUE)Following logs... (Ctrl+C to stop)$(NC)"
	@tail -f logs/collection.log

logs-clear: ## Clear all log files
	@echo "$(YELLOW)Clearing log files...$(NC)"
	@> logs/collection.log
	@echo "$(GREEN)✓ Logs cleared!$(NC)"

# Testing
test: ## Quick test (just collect once)
	@echo "$(BLUE)Running quick test...$(NC)"
	@echo ""
	@echo "$(BLUE)Collecting readings...$(NC)"
	@. venv/bin/activate && python source/collectors/hue_collector.py --collect-once

test-discover: ## Test with discovery + collection
	@echo "$(BLUE)Running discovery test...$(NC)"
	@echo ""
	@echo "$(BLUE)1. Discovering sensors...$(NC)"
	@. venv/bin/activate && python source/collectors/hue_collector.py --discover
	@echo ""
	@echo "$(BLUE)2. Collecting once...$(NC)"
	@. venv/bin/activate && python source/collectors/hue_collector.py --collect-once

test-full: ## Run full integration test
	@echo "$(BLUE)Running full integration test...$(NC)"
	@echo ""
	@echo "$(BLUE)1. Discovering sensors...$(NC)"
	. venv/bin/activate && python source/collectors/hue_collector.py --discover
	@echo ""
	@echo "$(BLUE)2. Collecting readings...$(NC)"
	. venv/bin/activate && python source/collectors/hue_collector.py --collect-once
	@echo ""
	@echo "$(BLUE)3. Verifying database...$(NC)"
	. venv/bin/activate && python3 -c "import sqlite3; conn = sqlite3.connect('data/readings.db'); cursor = conn.execute('SELECT COUNT(*) FROM readings'); count = cursor.fetchone()[0]; print(f'Total readings in database: {count}'); print('\033[0;32m✓ Test passed! Data was stored successfully.\033[0m' if count > 0 else '\033[0;31m✗ Test failed! No data in database.\033[0m'); conn.close()"

# Development tools
lint: ## Check Python files with pylint
	@echo "$(BLUE)Running pylint...$(NC)"
	. venv/bin/activate && pylint source/ --disable=C0111,C0103 || true

format: ## Format Python code with black
	@echo "$(BLUE)Formatting Python code with black...$(NC)"
	. venv/bin/activate && black source/ --line-length 100 --quiet

# Production Testing - 24 Hour Operation Tests (T101-T104)
health-check: ## Run comprehensive health check of system
	@echo "$(BLUE)Running health check...$(NC)"
	. venv/bin/activate && python source/health_check.py

verify-setup: ## Verify configuration and system setup (pre-collection check)
	@echo "$(BLUE)Verifying system setup...$(NC)"
	. venv/bin/activate && python source/verify_setup.py

evaluate: ## Run evaluation framework on collected data (SC-001, SC-002, SC-007)
	@echo "$(BLUE)Running evaluation framework on collected data...$(NC)"
	. venv/bin/activate && python source/evaluation.py

test-24hour-setup: ## T101: Start 24-hour continuous operation test
	@bash scripts/test-24hour-setup.sh

test-24hour-stop: ## Stop running 24-hour test gracefully
	@bash scripts/test-24hour-stop.sh

test-24hour-verify: ## T102-T104: Verify 24-hour test results (SC-001, SC-002, SC-007)
	@bash scripts/test-24hour-verify.sh

# Scheduled Collection (launchd) - macOS background collection
collection-init: ## Initialize launchd agents (one-time setup)
	@bash scripts/launchd-init.sh

collection-start: ## Start scheduled collection (every 5 minutes)
	@echo "$(BLUE)Starting scheduled collection...$(NC)"
	@launchctl load "$$HOME/.config/LaunchAgents/com.hometemperaturemonitoring.hue.plist" 2>/dev/null || true
	@launchctl load "$$HOME/.config/LaunchAgents/com.hometemperaturemonitoring.amazon.plist" 2>/dev/null || true
	@launchctl load "$$HOME/.config/LaunchAgents/com.hometemperaturemonitoring.nest.plist" 2>/dev/null || true
	@echo "$(GREEN)✓ Collection started! Runs every 5 minutes.$(NC)"

collection-stop: ## Stop scheduled collection
	@echo "$(BLUE)Stopping scheduled collection...$(NC)"
	@launchctl unload "$$HOME/.config/LaunchAgents/com.hometemperaturemonitoring.hue.plist" 2>/dev/null || echo "  (Hue agent not loaded)"
	@launchctl unload "$$HOME/.config/LaunchAgents/com.hometemperaturemonitoring.amazon.plist" 2>/dev/null || echo "  (Amazon agent not loaded)"
	@launchctl unload "$$HOME/.config/LaunchAgents/com.hometemperaturemonitoring.nest.plist" 2>/dev/null || echo "  (Nest agent not loaded)"
	@echo "$(GREEN)✓ Collection stopped!$(NC)"

collection-status: ## Show scheduled collection status
	@echo "$(BLUE)Scheduled Collection Status:$(NC)"
	@launchctl list | grep -i hometemperaturemonitoring || echo "  No agents loaded"

collection-logs: ## View scheduled collection logs
	@echo "$(BLUE)Following collection logs (Ctrl+C to stop)...$(NC)"
	@tail -f logs/collection.log 2>/dev/null || echo "  (No logs yet - run: make collection-start)"

# Structured Log Analysis (Phase 5)
log-view: ## View structured JSON logs with pretty-printing (jq colors)
	@echo "$(BLUE)Viewing structured logs (combined collection.log):$(NC)"
	@echo ""
	@cat logs/collection.log 2>/dev/null | grep '^{' | jq -C '.' | tail -50 2>/dev/null || echo "$(YELLOW)No logs found. Run 'make collection-start' to begin collecting.$(NC)"

log-errors: ## Filter and show only ERROR level entries from structured logs
	@echo "$(BLUE)Error entries from structured logs:$(NC)"
	@echo ""
	@cat logs/collection.log 2>/dev/null | grep '^{' | jq -C 'select(.level == "ERROR")' 2>/dev/null | tail -50 || echo "$(YELLOW)No errors found!$(NC)"

log-stats: ## Generate summary statistics from structured logs
	@echo "$(BLUE)Log Analysis & Statistics:$(NC)"
	@echo ""
	@. venv/bin/activate && python3 source/utils/log_parser.py logs/collection.log 2>/dev/null || echo "$(YELLOW)No logs available yet.$(NC)"

log-json: ## Pretty-print raw JSON logs
	@echo "$(BLUE)Raw structured logs (pretty-printed):$(NC)"
	@echo ""
	@cat logs/collection.log 2>/dev/null | grep '^{' | jq 'select(.)' -C 2>/dev/null | head -100 || echo "$(YELLOW)No logs found.$(NC)"

collection-uninstall: ## Remove launchd agents completely
	@bash scripts/launchd-cleanup.sh

.DEFAULT_GOAL := help
