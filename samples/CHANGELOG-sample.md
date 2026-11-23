# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.2.0] - 2026-11-23

### Added
- User profile settings modal (`7f89a1c`)
- Webhook notification support for failed builds (`3e45b12`)
- Export data to CSV and JSON formats (`9a12c45`)

### Fixed
- Prevent crash on unexpected null database connection pool (`a1b2c3d`)
- Correct timezone offset calculation in session scheduler (`e4f5a6b`)
- Fix OAuth token refresh race condition (`1234abc`)

### Changed
- Migrate authentication middleware to use JWT bearer tokens (`89cdef0`)
- Optimize query performance for repository activity feed (`5678def`)
- Update dependency pyyaml to 6.0.2 (`bcdef01`)

### Removed
- Drop legacy v1 authentication endpoints (`cdef012`)
- Remove deprecated CLI flag `--legacy-mode` (`def0123`)

## [v1.1.0] - 2026-10-15

### Added
- Multi-factor authentication via TOTP (`a4b3c2d`)
- Dark mode toggle in user preferences (`e7d6c5b`)

### Fixed
- Resolve memory leak in long-lived background workers (`b8a9c0d`)

### Changed
- Refactor notification service to use async message queue (`c1d2e3f`)

## [v1.0.0] - 2026-09-01

### Added
- Initial project release with core API and CLI tooling (`f0e1d2c`)
