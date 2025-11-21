# Makefile Guide

This project includes a comprehensive Makefile for easy testing, development, and operations.

## Quick Start

```bash
# View all available commands
make help

# Run a quick test (discovery + one collection)
make test-quick

# Collect readings once
make collect-once

# View recent readings
make db-view
```

## Command Categories

### Setup & Environment

```bash
make setup          # Install dependencies and setup virtual environment
make clean          # Remove all build, test, and cache artifacts
```

### Authentication & Configuration

```bash
# Automatic discovery (recommended)
make auth

# Manual IP address
make auth-ip HUE_IP=192.168.1.105
```

### Discovery & Collection

```bash
make discover       # List all temperature sensors
make collect-once   # Collect readings once and store in database
make continuous     # Run continuous collection (Ctrl+C to stop)
```

### Database Operations

```bash
make db-reset       # Delete and recreate empty database
make db-view        # View recent readings (last 20)
make db-stats       # Show database statistics
make db-query SQL="SELECT * FROM readings LIMIT 5"  # Custom SQL
```

### Logs

```bash
make logs           # Show recent 50 log entries
make logs-tail      # Follow logs in real-time (Ctrl+C to stop)
make logs-clear     # Clear all log files
```

### Health Check & Setup Verification

```bash
make health-check   # Run comprehensive health check of system
make verify-setup   # Verify configuration and system setup (pre-collection check)
```

### Evaluation & Testing

```bash
make evaluate       # Run evaluation framework on collected data (SC-001, SC-002, SC-007)
```

### Testing

```bash
make test           # Full integration test (discover, collect, verify)
make test-quick     # Quick test (discovery + one collection)
```

### Health & Verification

```bash
make health-check   # Comprehensive system health check
make verify-setup   # Verify configuration before collection
```

### Evaluation & Analysis

```bash
make evaluate       # Run evaluation framework on collected data
make log-stats      # Generate summary statistics from logs
```

### Development

```bash
make lint           # Check Python files with pylint
make format         # Format Python code with black
```

## Usage Examples

### One-Off Tests

```bash
# Test discovery works
make discover

# Test a single collection cycle
make collect-once

# Verify data storage
make db-view
make db-stats
```

### Short Runs

```bash
# Quick integration test (30 seconds)
make test-quick

# Collect readings for 5 minutes (default interval)
make continuous
  # Press Ctrl+C after desired time
```

### Reset and Restart

```bash
# Clear all database
make db-reset

# Clear all logs
make logs-clear

# Full clean
make clean
```

### Database Queries

```bash
# View recent readings
make db-view

# Show statistics per sensor
make db-stats

# Custom query
make db-query SQL="SELECT AVG(temperature_celsius) FROM readings"

# Export to CSV
make db-query SQL="SELECT timestamp, device_id, temperature_celsius FROM readings" > readings.txt
```

## Tips

- All commands activate the virtual environment automatically
- Use `make help` to see descriptions of all commands
- Commands are color-coded: Blue=actions, Green=success, Yellow=info, Red=errors
- Most commands have built-in error checking and helpful messages
- Database commands work even if no readings exist yet

## Troubleshooting

### "No such file or directory" errors

The virtual environment may not be set up. Run:
```bash
make setup
```

### Database is locked

If you get "database is locked" errors, the retry logic should handle it. If persistent:
```bash
make db-reset
```

### Permissions denied on Makefile

Make sure the file exists and is readable:
```bash
ls -l Makefile
```

## Integration with CI/CD

The Makefile can be used in CI/CD pipelines:

```bash
# In a GitHub Actions workflow:
make setup
make test-quick
make db-stats
```

## Notes

- The `venv` directory is created automatically on first `make setup`
- All database operations use `data/readings.db`
- Logs are displayed in real-time during execution
- Color output works in most terminals (set `NO_COLOR=1` to disable)

