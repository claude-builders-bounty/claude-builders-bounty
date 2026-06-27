# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2024-03-27

### Added
- feat(auth): implement JWT token refresh mechanism
- feat(dashboard): add real-time analytics widgets
- feat(api): add rate limiting middleware with Redis
- feat(ui): dark mode toggle with system preference detection
- feat(db): database connection pooling for better performance
- feat(email): transactional email service with SendGrid
- feat(search): full-text search with SQLite FTS5

### Changed
- refactor(core): improve error handling patterns with custom Error classes
- chore(deps): update all dependencies to latest stable versions
- docs(readme): update installation instructions for v2.0
- style(components): apply consistent Prettier formatting
- test(unit): increase test coverage from 72% to 85%
- ci(github): add automated release workflow with semantic-release
- perf(api): optimize database queries with proper indexing

### Fixed
- fix(auth): resolve login redirect loop on OAuth callback
- fix(db): handle connection timeout gracefully with retry logic
- fix(api): correct pagination offset calculation for large datasets
- fix(ui): fix responsive layout on tablets and mobile devices
- fix(email): resolve email template rendering issues in Outlook
- fix(search): fix search results ranking algorithm

### Removed
- remove(legacy): deprecate v1 API endpoints (migration guide available)
- remove(deprecated): remove unused utility functions from lib/utils
- remove(old-ui): remove legacy dashboard components