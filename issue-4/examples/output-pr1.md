## Summary
The changes add a safeguard for null webhook payloads and normalize status mapping before notification dispatch. The PR also improves logging around webhook retries.

## Risks
- Retry behavior could increase duplicate notifications if idempotency keys are missing.
- Mapping defaults may hide unknown statuses if not monitored.

## Improvement Suggestions
- Add a regression test for duplicate webhook delivery.
- Emit a metric when an unknown status falls back to default mapping.

## Confidence
Medium
