# Quickstart: Production-Ready System Reliability

## Health Check Usage
- Run health check: `python source/health_check.py`
- Output: Pass/fail/critical, remediation guidance, exit codes (0/1/2)
- Timeout: 15 seconds enforced

## Monitoring Alert Files
- OAuth alert: `data/ALERT_TOKEN_REFRESH_NEEDED.txt` (created on permanent auth error)
- Log rotation status: check `logs/` for rotated files and disk usage
- Retry events: check logs for diagnostic context

## Performance Baseline Guidance
- Capture baseline: `python source/utils/performance.py --capture-baseline`
- Compare after optimization: `python source/utils/performance.py --compare-baseline`
- Targets: 30% faster cycle, 50% smaller payload

## Device Naming CLI Commands
- Set device name: `python source/storage/device_manager.py --set-name <device_id> <name>`
- Amend device name: `python source/storage/device_manager.py --amend-name <device_id> <name> [--recursive]`
- List devices: `python source/storage/device_manager.py --list-devices`

---

**Integration Scenarios:**
- Run both collectors for 24 hours, monitor for database locked errors, retry events, log rotation, and data gaps
- Simulate network/API failures to verify retry logic and alerting
- Validate health check against all failure scenarios
- Confirm device registry and naming features via CLI and readings
