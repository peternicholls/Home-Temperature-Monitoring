.PHONY: help setup clean test auth discover collect collect-once continuous db-reset db-query db-view logs tail

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
	@echo "$(GREEN)Authentication & Configuration:$(NC)"
	@echo "  make auth           - Authenticate with Hue Bridge (press button when prompted)"
	@echo "  make auth-ip        - Authenticate with manual Bridge IP (set HUE_IP=192.168.1.x)"
	@echo ""
	@echo "$(GREEN)Discovery & Collection:$(NC)"
	@echo "  make discover       - List all temperature sensors"
	@echo "  make collect-once   - Collect readings once and store in database"
	@echo "  make continuous     - Run continuous collection (Ctrl+C to stop)"
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
	@echo "  make test           - Run full integration test (auth, discover, collect, store)"
	@echo "  make test-quick     - Quick test (just discovery and one collection)"
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

# Discovery & Collection
discover: ## List all temperature sensors
	@echo "$(BLUE)Discovering temperature sensors...$(NC)"
	. venv/bin/activate && python source/collectors/hue_collector.py --discover

collect-once: ## Collect readings once and store in database
	@echo "$(BLUE)Running single collection cycle...$(NC)"
	. venv/bin/activate && python source/collectors/hue_collector.py --collect-once

continuous: ## Run continuous collection (Ctrl+C to stop)
	@echo "$(BLUE)Starting continuous collection mode...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	. venv/bin/activate && python source/collectors/hue_collector.py --continuous

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
	. venv/bin/activate && python3 -c "import sqlite3; conn = sqlite3.connect('data/readings.db'); cursor = conn.execute('SELECT device_id, temperature_celsius, timestamp FROM readings ORDER BY timestamp DESC LIMIT 20'); print(f\"{'Device ID':<50} {'Temp (°C)':<12} {'Timestamp':<30}\"); print('-' * 92); [print(f\"{d:<50} {t:<12.2f} {ts:<30}\") for d, t, ts in cursor.fetchall()]; conn.close()"

db-stats: ## Show database statistics
	@echo "$(BLUE)Database Statistics:$(NC)"
	. venv/bin/activate && python3 -c "import sqlite3; conn = sqlite3.connect('data/readings.db'); cursor = conn.execute('SELECT COUNT(*) FROM readings'); print(f'Total readings: {cursor.fetchone()[0]}\n'); cursor = conn.execute('SELECT device_id, COUNT(*) as count, MIN(temperature_celsius) as min_temp, MAX(temperature_celsius) as max_temp, AVG(temperature_celsius) as avg_temp FROM readings GROUP BY device_id ORDER BY device_id'); print(f\"{'Device ID':<50} {'Count':<8} {'Min':<8} {'Max':<8} {'Avg':<8}\"); print('-' * 82); [print(f\"{d:<50} {c:<8} {mi:<8.1f} {ma:<8.1f} {a:<8.1f}\") for d, c, mi, ma, a in cursor.fetchall()]; conn.close()"

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
test: ## Run full integration test
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

test-quick: ## Quick test (discovery + one collection)
	@echo "$(BLUE)Running quick test...$(NC)"
	@echo ""
	@echo "$(BLUE)1. Discovering sensors...$(NC)"
	@. venv/bin/activate && python source/collectors/hue_collector.py --discover
	@echo ""
	@echo "$(BLUE)2. Collecting once...$(NC)"
	@. venv/bin/activate && python source/collectors/hue_collector.py --collect-once

# Development tools
lint: ## Check Python files with pylint
	@echo "$(BLUE)Running pylint...$(NC)"
	. venv/bin/activate && pylint source/ --disable=C0111,C0103 || true

format: ## Format Python code with black
	@echo "$(BLUE)Formatting Python code with black...$(NC)"
	. venv/bin/activate && black source/ --line-length 100 --quiet

.DEFAULT_GOAL := help
