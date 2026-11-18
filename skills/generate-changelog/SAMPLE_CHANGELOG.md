# Changelog

## [v1.4.0] - 2026-11-19
_Changes since tag `v1.3.0`_

### Added
- feat(auth): add WebAuthn passkey enrollment flow (`8f3c21a`)
- feat(billing): support per-seat prorated upgrades via Stripe webhooks (`4d19b02`)

### Fixed
- fix(api): prevent race condition during concurrent idempotency-key writes (`a290f4e`)
- fix(ui): restore keyboard focus trap inside confirmation dialog (`c1087bd`)

### Changed
- refactor(db): migrate session cleanup query to indexed batch delete (`e45b110`)
- docs(readme): update local Quickstart environment variables (`91ab30c`)

### Removed
- remove(legacy): drop deprecated v1 XML export endpoint (`771de09`)
