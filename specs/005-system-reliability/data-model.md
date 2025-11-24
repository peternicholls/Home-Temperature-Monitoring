# Data Model: Production-Ready System Reliability

**Entities:**
- HealthReport
- RetryEvent
- PerformanceMetrics
- LogRotationStatus
- OAuthAlert
- DeviceRegistry
- DeviceNaming

## HealthReport
- id
- timestamp
- status (pass/fail/critical)
- component_results (dict)
- remediation_guidance (str)

## RetryEvent
- id
- timestamp
- operation (str)
- error_type (transient/permanent)
- attempt_number (int)
- backoff_time (float)
- success (bool)
- diagnostic_context (str)

## PerformanceMetrics
- id
- timestamp
- collection_cycle_duration (float)
- network_payload_size (int)
- baseline_comparison (str)
- concurrent_measurement_id (str)

## LogRotationStatus
- id
- timestamp
- log_file (str)
- rotated (bool)
- disk_usage_mb (float)
- backup_count (int)
- error (str)

## OAuthAlert
- id
- timestamp
- alert_type (token_refresh_needed, permanent_auth_error)
- file_created (bool)
- email_sent (bool)
- cleared_on_success (bool)

## DeviceRegistry
- device_id (PK)
- device_type
- device_name
- location
- unique_id
- model_info
- first_seen
- last_seen
- is_active

## DeviceNaming
- device_id
- name
- amended (bool)
- recursive_update (bool)
- history_updated (bool)

---

**Relationships:**
- HealthReport aggregates component_results from all validators
- RetryEvent links to operations in collectors/storage
- PerformanceMetrics links to collection cycles and baseline comparisons
- LogRotationStatus links to log files and disk usage
- OAuthAlert links to Amazon AQM collector events
- DeviceRegistry links to readings and collectors
- DeviceNaming links to registry and readings
