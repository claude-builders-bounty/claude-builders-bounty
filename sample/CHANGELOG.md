# Changelog

## [v1.2.0] - 2026-07-20

### Added
- user dashboard with team management
- dark mode toggle in settings
- pagination component for data tables
- export to CSV for reports

### Fixed
- sidebar collapsing on mobile viewport
- authentication token refresh race condition
- date picker timezone offset error
- missing validation on email change form

### Changed
- database query layer to use prepared statements
- onboarding flow with reduced steps

### Removed
- deprecated v1 API endpoints
- legacy cookie-based session handling

## [v1.1.0] - 2026-06-15

### Added
- team invitation system
- audit log for admin actions

### Fixed
- memory leak in WebSocket connections
- incorrect currency formatting in invoice

### Changed
- upgrade Next.js from 14 to 15
- rate limiting from in-memory to Redis-backed

## [v1.0.0] - 2026-05-01

### Added
- user authentication with email/password and OAuth
- project CRUD with real-time collaboration
- role-based access control
- Stripe payment integration
- notification system (email + in-app)
- search with full-text indexing
