# Phase 0 Research: Alexa AQM Integration

## Unknowns & Clarifications

- **Python Version**: Recommend Python 3.10+ for alexapy compatibility and security.
- **Additional Libraries**: Required: requests, PyYAML, sqlite3 (standard lib), logging (standard lib).
- **Data Storage**: Air quality readings and logs will be stored in SQLite (per constitution), with credentials in `config/secrets.yaml`.
- **Testing Framework**: Use pytest for unit/integration tests; manual verification for device access.
- **Deployment**: Local execution on macOS/Linux/Windows; no cloud deployment required.
- **User/Device Volume**: Initial scope is single user, single/multiple devices per session; scalable to more users/devices if needed.
- **Regulatory/Security Constraints**: Credentials must be encrypted in `secrets.yaml`; follow local security best practices.

## Decisions & Rationale

- **Language/Version**: Python 3.10+ (widely supported, compatible with alexapy)
- **Dependencies**: alexapy (Amazon auth/device API), requests (HTTP), PyYAML (config), sqlite3 (data), logging (errors)
- **Storage**: SQLite for readings/logs; YAML for secrets/config
- **Testing**: pytest for automated tests; manual for device flows
- **Platform**: Local execution only
- **Performance**: Targets from spec (95% auth success, 90% data retrieval <2min, etc.)
- **Constraints**: 120s timeout, 5 retries (exponential backoff), secure credential storage
- **Scale/Scope**: Single user, multi-device; extensible

## Alternatives Considered

- **Other Languages**: Node.js, Go, Rust (rejected: less mature libraries for Alexa integration)
- **Other Storage**: CSV, direct file logging (rejected: not analysis-ready, less robust)
- **Other Testing**: unittest (pytest preferred for features/plugins)
- **Cloud Deployment**: Not required; local preferred for privacy/security

## Justifications for Constitution Deviations

- **5 Retries**: Amazon API/network reliability issues justify more retries than constitution default (3); improves robustness.
- **Composite Device ID**: Will use `alexa:<device_id>` format for all Alexa devices to ensure schema compliance and cross-device consistency.
- **Schema Mapping**: Alexa readings will be mapped to SQLite schema: timestamp, device_id, temperature, location, device_type.
- **Validation**: All readings will be validated against constitution rules (temperature range, required fields).

---

All clarifications resolved. Ready for Phase 1 design.
