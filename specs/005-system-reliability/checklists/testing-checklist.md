# Testing Checklist: Sprint 005

- [ ] All foundational tests written and fail before implementation
- [ ] Retry logic tests cover all scenarios (success, transient, permanent, exhaustion, rate limit, logging, concurrency)
- [ ] Performance tests cover cycle duration, payload size, baseline, logging, concurrency
- [ ] Health check tests cover all components, exit codes, timeout, security
- [ ] Database WAL tests cover init, checkpoint, growth, concurrency
- [ ] Collector retry tests cover network, API, rate limit, exhaustion, logging
- [ ] Log rotation tests cover threshold, integrity, backup, disk usage, low space, concurrency, errors, retry
- [ ] Health check validation suite covers all failure scenarios
- [ ] API optimization tests cover baseline, sensors-only, payload, duration, fallback, latency
- [ ] 24-hour integration test executed
- [ ] 80%+ coverage verified for all new code
