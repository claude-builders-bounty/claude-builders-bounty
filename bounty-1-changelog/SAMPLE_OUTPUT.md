# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v2.4.1] - 2026-05-12

### Added
- Add OAuth2 PKCE flow for mobile clients (a3f82c1)
- Implement rate limiting middleware with sliding window (7b1d4e9)
- Add bulk export endpoint for analytics data (e92ca3f)
- Introduce dark mode toggle in user preferences (4d8f1a2)
- Support WebSocket connections for real-time notifications (c5e7b30)

### Fixed
- Fix race condition in session token refresh (1f4a8d2)
- Resolve memory leak in connection pool under high concurrency (8c2e6f1)
- Correct pagination offset calculation for filtered queries (3a9d7b5)
- Fix CORS headers not applied to preflight requests (6e1c4a8)

### Changed
- Refactor database migration runner to support rollbacks (b4c91e7)
- Update Node.js minimum version to 20 LTS (d7f2a35)
- Improve search query performance with trigram indexes (5e8b1c9)
- Migrate CI pipeline from CircleCI to GitHub Actions (9a3f6d2)
- Upgrade dependencies to patch known CVEs (2c7e4b8)
- Update API documentation for v2.4 endpoints (f1d8a93)

### Removed
- Remove deprecated v1 authentication endpoints (0b5c2e4)
- Drop support for Node.js 16 (7d4f9a1)

## [v2.4.0] - 2026-04-28

### Added
- Add team management API with role-based access control (cc81f4a)
- Implement CSV import for batch user creation (2e9a7d3)

### Fixed
- Fix timezone handling in scheduled report generation (5b3c8e1)

### Changed
- Refactor logging to use structured JSON format (a1d4f72)
- Update rate limit response to include retry-after header (8f2b6c9)
