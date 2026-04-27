# Changelog

## [1.2.0] - 2026-04-27

### Added
- New user authentication via OAuth2
- Dark mode theme support
- Real-time WebSocket notifications

### Fixed
- Login redirect loop on expired sessions
- Memory leak in WebSocket connection pool
- Broken pagination on large datasets

### Changed
- Upgrade Express.js from v4 to v5
- API rate limit increased from 100 to 500 req/min
- Refactored database layer to use connection pooling

### Removed
- Deprecated v1 API endpoints
- Legacy jQuery dependencies
- Unused test fixtures
