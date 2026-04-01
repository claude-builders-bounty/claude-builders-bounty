# Changelog

## [1.4.0] - 2026-04-01

### Added

- user authentication with OAuth2 support (`a1b2c3d`)
- dark mode toggle for dashboard (`e4f5a6b`)
- CSV export for analytics reports (`c7d8e9f`)

### Fixed

- race condition in WebSocket reconnection logic (`1a2b3c4`)
- incorrect timezone offset for EU users (`5d6e7f8`)

### Changed

- upgrade dependencies to latest versions (`9a0b1c2`)
- refactor database connection pooling (`d3e4f5a`)
- update API rate limiting to 1000 req/min (`6b7c8d9`)

### Removed

- legacy v1 API endpoints (`e0f1a2b`)
- unused jQuery dependency (`3c4d5e6`)
