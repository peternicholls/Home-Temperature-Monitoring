# Code Review – Amazon Alexa AQM Integration

## Overview
Review covers the Sprint 2–3 implementation for the Amazon Alexa Air Quality Monitor (AQM) lifecycle: collectors, authentication flow, configuration, documentation, and supporting tooling. The goal was to verify reliability, test coverage, and alignment between code and docs. Below are the significant findings and actionable recommendations.

## Findings

### 1. Async Collector Blocks the Event Loop
- `source/collectors/amazon_collector.py` declares `async` methods (`list_devices`, `get_air_quality_readings`, `collect_and_store`) but each uses synchronous `requests` calls and `time.sleep`. Every retry or request blocks the event loop, so `amazon_aqm_collector_main.py` cannot keep accurate intervals or respond quickly to cancellation.
- **Impact:** Continuous collection pauses for network latency/backoff, preventing other coroutines (or even the signal handler in `collect_continuous`) from running.
- **Recommendation:** Either switch to an async HTTP client (e.g., `httpx.AsyncClient`) and await requests, or make the collector synchronous and run it via `asyncio.to_thread`/executors. Replace `time.sleep` with `await asyncio.sleep` in any async code.

### 2. Amazon Config Settings Never Applied
- Retry/backoff/timeout values are read from `config['collection']`/`config['collection']['max_timeout']`, while docs and `config/config.yaml` place AQM settings under `collectors.amazon_aqm`.
- **Impact:** User-tuned values in `collectors.amazon_aqm` (interval, retries, backoff) are silently ignored unless the main script manually normalizes the config. CLI users and tests receive default settings only.
- **Recommendation:** Normalize configuration when loading (e.g., move `collectors.amazon_aqm` into a top-level `amazon_aqm` block) or update the collector to read from `config['collectors']['amazon_aqm']`. Update docs/specs to match the actual structure and add validation.

### 3. Cookie Capture Web UI Hard-Codes amazon.co.uk
- `source/web/app.py` always calls `run_amazon_login()` without a domain, and the helper defaults to `amazon.co.uk`.
- **Impact:** Users on `amazon.com`, `amazon.de`, etc., capture cookies for the wrong origin, so API calls fail even though the UI reports success.
- **Recommendation:** Read the target domain from `config/config.yaml` (or accept it via the POST request) and pass it through to `run_amazon_login`. Validate domain mismatches before saving cookies.

### 4. Missing Runtime Dependencies
- README instructs users to run the Flask web UI and Playwright automation, but `requirements.txt` only includes PyYAML, phue, requests, Playwright, and pytest packages. Flask is missing, so `python source/web/app.py` fails on `ModuleNotFoundError`.
- **Recommendation:** Add `Flask` (and related deps if pinning) to `requirements.txt`. Consider a `make setup` step that also runs `playwright install` so browser binaries are present before users run the login flow.

### 5. Quickstart Documentation Does Not Match the Code
- `specs/004-alexa-aqm-integration/quickstart.md` examples:
  - Load cookies from `config` instead of `config/secrets.yaml`.
  - Instantiate `AmazonAQMCollector(config)` without passing cookies (required positional arg).
  - Refer to fields like `device['name']`, `device['serial_number']`, `readings.get(4, {})`, and parameters such as `serial_number=` that do not exist in the implementation.
- **Impact:** Copy-pasting these snippets raises errors immediately, undermining confidence in the docs.
- **Recommendation:** Rewrite the quickstart examples so they reflect the actual API (friendly_name/device_serial keys, readings with named fields, cookies pulled from secrets). Validate each example by running it.

### 6. Playwright Install Step Missing
- After `pip install playwright`, the first browser launch fails unless `playwright install` (and possibly `playwright install-deps`) is run.
- **Recommendation:** Update README/quickstart/setup instructions (and optionally the Makefile `setup` target) to perform the Playwright install step.

### 7. No Automated Tests for Amazon Collector
- `tests/test_amazon_aqm.py` is actually a manual script that reads real secrets and defines no `test_*` functions, yet docs claim `pytest tests/test_amazon_aqm.py -v` runs unit tests.
- **Impact:** CI and developers get a green test suite even if core AQM functionality regresses. Manual script also risks leaking real credentials if accidentally committed.
- **Recommendation:** Move the script into `tests/manual/` or `scripts/`, and create proper unit/integration tests that mock the GraphQL/Phoenix endpoints plus the database layer. Ensure Pytest discovers and executes them.

## Next Steps
1. Decide on an async vs synchronous collector strategy and implement non-blocking retries.
2. Align configuration loading with documentation so AQM-specific settings work as advertised.
3. Update the web UI login flow to respect the configured Amazon region.
4. Expand `requirements.txt` and setup docs to include Flask and Playwright browser installs.
5. Overhaul the quickstart samples to match real inputs/outputs, verifying each snippet.
6. Add automated tests for collector discovery, Phoenix parsing, validation, and DB formatting; keep manual scripts separate.

Addressing these items will make the Alexa AQM lifecycle more reliable, easier to set up, and better covered by tests/documentation.
