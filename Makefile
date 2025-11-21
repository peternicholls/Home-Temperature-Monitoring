.PHONY: help setup clean auth auth-ip discover collect-once continuous aqm-setup aqm-discover aqm-collect aqm-continuous aqm-test web-start web-stop db-reset db-query db-view db-stats logs logs-tail logs-clear test test-discover test-full test-24hour-setup test-24hour-stop test-24hour-verify collection-init collection-start collection-stop collection-status collection-logs collection-uninstall lint format health-check

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
	@echo ""
	@echo "$(GREEN)Health Check:$(NC)"
	@echo "  make health-check   - Run comprehensive health check of system"
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
	@echo "$(GREEN)Logs:$(NC)"
	@echo "  make logs           - Show recent log entries"
	@echo "  make logs-tail      - Follow logs in real-time (Ctrl+C to stop)"
	@echo "  make logs-clear     - Clear all log files"
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
	. venv/bin/activate && python3 -c "import sqlite3; conn = sqlite3.connect('data/readings.db'); cursor = conn.execute('SELECT device_id, device_type, temperature_celsius, humidity_percent, pm25_ugm3, voc_ppb, co_ppm, iaq_score, timestamp FROM readings ORDER BY timestamp DESC LIMIT 20'); print(f\"{'Device ID':<40} {'Type':<12} {'Temp':<8} {'Hum%':<8} {'PM2.5':<8} {'VOC':<8} {'CO':<8} {'IAQ':<8} {'Timestamp':<20}\"); print('-' * 150); [print(f\"{d:<40} {dt:<12} {t:<8.1f} {h if h else '-':<8} {p if p else '-':<8} {v if v else '-':<8} {c if c else '-':<8} {i if i else '-':<8} {ts[:19]:<20}\") for d, dt, t, h, p, v, c, i, ts in cursor.fetchall()]; conn.close()"

db-stats: ## Show database statistics
	@echo "$(BLUE)Database Statistics:$(NC)"
	. venv/bin/activate && python3 -c "import sqlite3; conn = sqlite3.connect('data/readings.db'); cursor = conn.execute('SELECT COUNT(*) FROM readings'); print(f'Total readings: {cursor.fetchone()[0]}\n'); cursor = conn.execute('SELECT device_type, COUNT(*) FROM readings GROUP BY device_type'); print('Readings by device type:'); [print(f'  {dt}: {c}') for dt, c in cursor.fetchall()]; print(); cursor = conn.execute('SELECT device_id, device_type, COUNT(*) as count, MIN(temperature_celsius) as min_temp, MAX(temperature_celsius) as max_temp, AVG(temperature_celsius) as avg_temp FROM readings GROUP BY device_id, device_type ORDER BY device_id'); print(f\"{'Device ID':<45} {'Type':<12} {'Count':<8} {'Min°C':<8} {'Max°C':<8} {'Avg°C':<8}\"); print('-' * 95); [print(f\"{d:<45} {dt:<12} {c:<8} {mi:<8.1f} {ma:<8.1f} {a:<8.1f}\") for d, dt, c, mi, ma, a in cursor.fetchall()]; conn.close()"

# Logs
logs: ## Show recent log entries
	@echo "$(BLUE)Recent log entries:$(NC)"
	@tail -50 logs/hue_collection.log 2>/dev/null || echo "$(YELLOW)No logs yet$(NC)"

logs-tail: ## Follow logs in real-time (Ctrl+C to stop)
	@echo "$(BLUE)Following logs... (Ctrl+C to stop)$(NC)"
	@tail -f logs/hue_collection.log

logs-clear: ## Clear all log files
	@echo "$(YELLOW)Clearing log files...$(NC)"
	@> logs/hue_collection.log
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
	@echo "$(GREEN)✓ Collection started! Runs every 5 minutes.$(NC)"

collection-stop: ## Stop scheduled collection
	@echo "$(BLUE)Stopping scheduled collection...$(NC)"
	@launchctl unload "$$HOME/.config/LaunchAgents/com.hometemperaturemonitoring.hue.plist" 2>/dev/null || echo "  (Hue agent not loaded)"
	@launchctl unload "$$HOME/.config/LaunchAgents/com.hometemperaturemonitoring.amazon.plist" 2>/dev/null || echo "  (Amazon agent not loaded)"
	@echo "$(GREEN)✓ Collection stopped!$(NC)"

collection-status: ## Show scheduled collection status
	@echo "$(BLUE)Scheduled Collection Status:$(NC)"
	@launchctl list | grep -i hometemperaturemonitoring || echo "  No agents loaded"

collection-logs: ## View scheduled collection logs
	@echo "$(BLUE)Following Hue scheduled logs (Ctrl+C to stop)...$(NC)"
	@tail -f logs/hue_scheduled.log 2>/dev/null || echo "  (No logs yet - run: make collection-start)"

collection-uninstall: ## Remove launchd agents completely
	@bash scripts/launchd-cleanup.sh

.DEFAULT_GOAL := help
