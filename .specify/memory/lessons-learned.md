---
description: "Critical knowledge base of lessons learned. AGENTS MUST READ THIS before planning or implementing features."
last_updated: "2025-11-21"
sprints_covered: "003, 005"
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
- **Mocking Strategy**:
  - **Patch Location**: Patch where an object is *imported*, not where it is defined.
  - **Stateful Mocks**: Use `side_effect` (sequences of exceptions/values) to test retry and fallback logic.
- **Performance Testing**:
  - **Tolerances**: Use relative improvements and tolerances (±50ms), not strict timings.
  - **Targeted Coverage**: Measure coverage on the specific module being optimized, not the entire codebase.
- **Production-Realistic Test Data Prevents False Positives**: Small test files (<1KB) can expose edge cases in libraries (like Python's `RotatingFileHandler`) that don't reflect production behavior. Production-realistic file sizes (5KB+) eliminate false positives. For file operations use 5KB+ files, for database tests use representative row counts, for network tests use actual API response sizes. Small test data can hide critical bugs that only manifest at production scale. **Source**: Sprint 005, Phase 5 (Log Rotation) **Date**: 2025-11-21
- **Integration Tests for Failure Modes**: Integration tests that simulate realistic failure modes (network disconnection, rate limiting, database contention) provide higher confidence than unit tests with mocks. Real failure scenarios reveal edge cases that mocks miss. Balance unit tests (fast, isolated) with integration tests (slower, realistic). For critical reliability features (retry logic, error handling, health checks), prioritize integration tests that simulate real failure modes. **Source**: Sprint 005, Phase 8 (Integration Testing) **Date**: 2025-11-21

## 2. Architecture & Resilience

- **Error Classification**: Distinguish between `TransientError` (retryable, e.g., network blip) and `PermanentError` (fail fast, e.g., file not found). **Action**: Implement explicit error hierarchies.
- **Graceful Degradation**: Partial failures (e.g., one Hue sensor failing) must not crash the entire collection process. **Action**: Catch exceptions at the item level and continue.
- **Thread Safety**: Python's `logging` is thread-safe, but custom logic (like rotation) requires explicit `threading.Lock()`.
- **Resilient Storage**:
  - **Write Verification**: Test database writes using transaction rollbacks to avoid side effects.
  - **Aliases**: Use class aliases (e.g., `StorageManager = DatabaseManager`) for backward compatibility during refactoring.
- **Caching**: Cache expensive operations (file I/O, API calls) using `@property` with lazy initialization.
- **Context Managers for Resources**: Always use Python context managers (`with` statement) for resources that require cleanup (timers, files, database connections, locks). Never rely on manual cleanup calls. This pattern prevents resource leaks, makes code more Pythonic and self-documenting, and ensures cleanup happens even when exceptions occur. **Source**: Sprint 005, Phase 2 (Performance Measurement) **Date**: 2025-11-21
- **Component Isolation in Validators**: Design validation systems as independent validators that can be tested and run separately. Provides specific, actionable remediation guidance for each failure type. Avoid monolithic check functions that fail fast and hide details. **Source**: Sprint 005, Phase 6 (Health Check) **Date**: 2025-11-21
- **Early Configuration Verification**: Always verify critical configuration settings (like WAL mode) on initialization rather than assuming they're correct. Log verification results for audit trails. Design graceful degradation paths for when settings are incorrect. **Source**: Sprint 005, Phase 3 (Database Resilience) **Date**: 2025-11-21

## 3. Performance & Optimization

- **Profile First**: Do not optimize without profiling. The M2 Ultra environment is powerful; premature optimization wastes time.
- **Baselines**: Capture performance baselines (`data/performance_baseline.json`) *before* optimizing to prove regression/improvement.
- **Type Safety**: When using context managers that populate values on exit, explicitly `assert value is not None` before using them in calculations to satisfy type checkers.
- **Exponential Backoff for Retry**: Always use exponential backoff for retry logic (1s, 2s, 4s), never fixed delays. Make backoff multiplier configurable to allow tuning for different APIs. Consider adding jitter to prevent synchronized retries across multiple instances. **Source**: Sprint 005, Phase 2 (Retry Logic) **Date**: 2025-11-21

## 4. Development Workflow & Operations

- **Research Phase**: For complex integrations (OAuth, GraphQL), create `research.md` and sequence diagrams *before* writing code.
- **Virtual Environment**: **ALWAYS** activate the virtual environment first: `source venv/bin/activate`.
- **Alerting**: Use file-based alerts (`data/ALERT_*.txt`) for critical failures to enable simple monitoring integration.
- **Async Testing**: Use `pytest-anyio` with the `asyncio` backend for async test support.
- **File-Based Alert Systems**: For critical alerts that require operator intervention, always provide a file-based alert mechanism in addition to optional notification channels (email, Slack, etc.). File-based alerts work everywhere, have zero dependencies, and enable simple monitoring integration. Alerts should auto-clear when issues are resolved. **Source**: Sprint 005, Phase 4 (Universal Retry Logic) **Date**: 2025-11-21

## 5. Security & Compliance

- **Credential Sanitization**: All logs, error messages, and health check outputs **MUST** redact credentials (API keys, tokens) using `[REDACTED]`.
- **Security TDD**: Write security tests (e.g., checking for leaked secrets) as part of the TDD cycle, not as an afterthought.

## 6. Action Items for Project Evolution

- [ ] Standardize error classification (Transient/Permanent base classes).
- [ ] Standardize alert file formats.
- [ ] Update Definition of Done to emphasize integration test reliability over unit test coverage.
