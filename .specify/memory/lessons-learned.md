---
description: "Critical knowledge base of lessons learned. AGENTS MUST READ THIS before planning or implementing features."
last_updated: "2025-11-21"
---

# Lessons Learned: Central Knowledge Base

**ATTENTION AI AGENTS**: This document captures critical lessons learned from previous development phases. It is essential reading for all agents involved in planning, implementing, and reviewing features. **You are required to apply these lessons** to avoid repeating past mistakes. 

1. **Before Starting Work**: Review relevant categories to avoid repeating past mistakes
2. **During Implementation**: Reference specific lessons when making architectural/technical decisions.
3. **After Completion**: After completing each phase implementation report, extract the "Lessons Learned" section and add it here with proper categorization and sprint/phase attribution.
4. **Periodic Review**: Revisit to identify patterns and update constitution/templates.

---

## 1. Testing Strategy & Quality

- **Integration > Unit**: Integration tests with real component interactions are more valuable than heavily-mocked unit tests. In Phase 6, integration tests were 100% reliable while unit tests failed due to mock complexity. **Action**: Prioritize integration tests for system validation.
- **Realistic Test Data**: Small test data (<1KB) hides bugs. Use production-realistic sizes (5KB+ for files, full JSON structures for APIs). **Action**: Mock data must mirror production complexity (e.g., full Hue Bridge config with rules/scenes, not just lights).
- **TDD Discipline**: Writing tests first catches edge cases (data loss in log rotation) and security gaps that implementation-first misses. **Action**: Write tests before implementation.
- **Early Comprehensive Testing** (Phase 8): Running failure mode simulations (T105-T111: network, API rate limiting, database locks, disk pressure, credentials, OAuth, file system errors) *before* extended duration tests identifies subtle timing issues invisible to multi-hour tests. **Action**: Include 5-8 distinct failure mode simulations in integration test phases before proceeding to 24+ hour duration tests.
- **Mocking Strategy**:
  - **Patch Location**: Patch where an object is *imported*, not where it is defined.
  - **Stateful Mocks**: Use `side_effect` (sequences of exceptions/values) to test retry and fallback logic.
- **Performance Testing**:
  - **Tolerances**: Use relative improvements and tolerances (±50ms), not strict timings.
  - **Targeted Coverage**: Measure coverage on the specific module being optimized, not the entire codebase.
- **Performance Baseline Establishment** (Phase 8): Without concrete before/after measurements, performance claims are subjective. Baselines must be captured on production/realistic hardware/network. Example: baseline (2.4s cycles, 185KB payload) vs optimized (1.6s cycles, 78KB payload) = 33% faster, 58% smaller. **Action**: Establish quantifiable baselines before optimization work and document hardware/network conditions for comparability.
## 2. Architecture & Resilience

- **Error Classification**: Distinguish between `TransientError` (retryable, e.g., network blip) and `PermanentError` (fail fast, e.g., file not found). **Action**: Implement explicit error hierarchies.
- **Graceful Degradation**: Partial failures (e.g., one Hue sensor failing) must not crash the entire collection process. **Action**: Catch exceptions at the item level and continue.
- **Graceful Degradation Requires Explicit Testing** (Phase 8): Failures don't cascade into system crashes only if explicitly tested. Tests T108 (disk pressure), T110 (token expiration), T111 (file system errors) and T055 (optional email notification) validated graceful degradation. Without explicit testing, "graceful" features silently fail. **Action**: For each critical feature, write explicit tests for "feature unavailable" scenarios and verify graceful degradation behavior.
- **Health Check Component Isolation** (Phase 8): When one validator fails, others must continue and be reported. This "isolation principle" prevents first-failure-hides-subsequent-issues problem. Implementation: try-catch wrapping each validator with aggregation in final step. **Action**: Design health checks with per-validator isolation and final aggregation step. This improves production debugging usability.
- **Thread Safety**: Python's `logging` is thread-safe, but custom logic (like rotation) requires explicit `threading.Lock()`.
- **Resilient Storage**:
  - **Write Verification**: Test database writes using transaction rollbacks to avoid side effects.
  - **Aliases**: Use class aliases (e.g., `StorageManager = DatabaseManager`) for backward compatibility during refactoring.
- **Caching**: Cache expensive operations (file I/O, API calls) using `@property` with lazy initialization.

## 3. Performance & Optimization

- **Profile First**: Do not optimize without profiling. The M2 Ultra environment is powerful; premature optimization wastes time.
- **Baselines**: Capture performance baselines (`data/performance_baseline.json`) *before* optimizing to prove regression/improvement.
- **Type Safety**: When using context managers that populate values on exit, explicitly `assert value is not None` before using them in calculations to satisfy type checkers.
- **Timeout Envelope Management** (Phase 8): When setting aggregate timeouts (e.g., 15-second health check with sub-component timeouts), account for component timeouts with 30%+ headroom. Hue Bridge timeout (5s) + Amazon timeout (10s) + other validators (≤3.5s) = 18.5s max, fits in 15s limit with careful timing. **Action**: Create timeout budget table (component → limit) and test each component against worst-case scenarios. Document timeout allocation across all validators.

## 4. Development Workflow & Operations

- **Research Phase**: For complex integrations (OAuth, GraphQL), create `research.md` and sequence diagrams *before* writing code.
- **Virtual Environment**: **ALWAYS** activate the virtual environment first: `source venv/bin/activate`.
- **Alerting**: Use file-based alerts (`data/ALERT_*.txt`) for critical failures to enable simple monitoring integration.
- **Async Testing**: Use `pytest-anyio` with the `asyncio` backend for async test support.
- **Concurrent Load vs Duration Testing** (Phase 8): Different test types reveal different problems. Concurrent load testing (multiple collectors writing simultaneously) uncovers race conditions and resource contention invisible to single-collector tests. Duration testing (24+ hours) validates stability under sustained load. Database lock scenarios appear under concurrent load but not in sequential scenarios. **Action**: Use separate test phases: (1) single-component validation, (2) multi-component concurrent validation, (3) duration validation. Each reveals different failure categories.
- **Structured Data Over String Formatting** (Phase 8B): Passing metadata as separate fields (reason, error_type, location) instead of embedding in message text makes data machine-readable and aggregatable. Before: `logger.warning(f"Sensor {location} is offline")` (text parsing needed). After: `logger.warning("Sensor offline", reason="unreachable", location=location)` (machine-queryable). **Action**: When logging errors/warnings, use structured fields for filtering. Reserve message field for context only.
- **Silent Operation for Production** (Phase 8B): Separator lines, emoji, and pretty-print in background process logs corrupt JSON parsing and break automated analysis. Decorator output in logs is a hidden technical debt. Production collectors should output only JSON to files, with Makefile commands or dashboards for human views. **Action**: For scheduled/background processes, enforce JSON-only output. Use build-time assertions (grep '^{' checks) to verify no decorative content.
- **Single-Line JSON Format Enforcement** (Phase 8B): Using `json.dump()` with improper settings sometimes wrapped long objects across multiple lines, breaking grep pipelines and line-based processing. Solution: `json.dumps(separators=(',', ':'))` guarantees single-line output. Verification: `grep '^{'` detects any wrapping. **Action**: Use dumps() not dump() for logs. Test with grep to verify no line wrapping.
- **Friendly Identifiers in Database Schema** (Phase 8B): Device IDs (e.g., `hue:00:17:88:01:02:02:b5:21-02-0402`) are necessary for uniqueness but opaque for humans. Adding a 'name' column with location names (e.g., "Utility") makes queries and reports usable. Supports both automation (device_id for matching) and manual inspection (name for reading). **Action**: Schema design should include both machine IDs and human-readable fields. This supports both programmatic access and ad-hoc queries.

## 5. Logging & Data Design

- **Message Strings vs Data Points** (Phase 8B): Embedding context in message text (e.g., `f"Sensor {location} is offline"`) requires text parsing. Structured data points with separate fields (message="Sensor offline", location=..., reason="unreachable") are queryable. Example: 46 warnings with reason="no_temperature_state" vs 23 with reason="unreachable" tells a complete story without parsing. **Action**: Always include structured metadata fields (reason, error_type, location, device_id) instead of text formatting.
- **Warning Breakdown by Category** (Phase 8B): Generic "48 warnings" offers no insight. Breaking down by reason code (46 no_temperature_state, 2 unreachable) enables root cause analysis. Example: overwhelming no_temperature_state warnings indicate discovery is returning non-temperature devices; unreachable warnings indicate connectivity issues. **Action**: Implement categorical breakdown in log analysis. Use reason/status codes for filtering.
- **Collector Consistency** (Phase 8B): Hue and Amazon collectors need identical logging patterns, schema fields, and output formats to ensure Makefile commands and analysis work uniformly. Inconsistency creates special cases in analysis tools. **Action**: Apply all logging/schema changes across all collectors simultaneously.

## 5. Security & Compliance

- **Credential Sanitization**: All logs, error messages, and health check outputs **MUST** redact credentials (API keys, tokens) using `[REDACTED]`.
- **Security TDD**: Write security tests (e.g., checking for leaked secrets) as part of the TDD cycle, not as an afterthought.

## 6. Action Items for Project Evolution

- [ ] Standardize error classification (Transient/Permanent base classes).
- [ ] Standardize alert file formats.
- [ ] Update Definition of Done to emphasize integration test reliability over unit test coverage.
