# Changelog

## [v1.1.0..HEAD] — 2026-07-18

### Added

- Add dark mode toggle with system preference detection (a1b2c3d)
- Implement keyboard shortcuts for navigation (e4f5g6h)
- Add export-to-PDF functionality for reports (i7j8k9l)

### Fixed

- Fix memory leak in websocket reconnection logic (m0n1o2p)
- Resolve race condition on concurrent file writes (q3r4s5t)
- Correct timestamp format in audit log entries (u6v7w8x)

### Changed

- Upgrade axios from 0.27 to 1.6 for security patches (y9z0a1b)
- Refactor state management to use Zustand instead of Context (c2d3e4f)
- Migrate CI pipeline from Travis to GitHub Actions (g5h6i7j)
- Update dependency graphql from 16.3 to 16.8 (k8l9m0n)

### Removed

- Deprecate legacy v1 REST API endpoints (o1p2q3r)
- Remove jQuery dependency in favor of vanilla JS (s4t5u6v)
- Drop support for Node.js 14 (w7x8y9z)

## [v1.0.0] — 2026-03-15

### Added

- Initial project scaffolding with Vite + React (a0b1c2d)
- User authentication with JWT and refresh tokens (e3f4g5h)
- Database schema with PostgreSQL migrations (i6j7k8l)
- RESTful API with Express.js route handlers (m9n0o1p)

### Fixed

- Fix CORS configuration for production deployment (q2r3s4t)
- Correct validation error messages in user registration form (u5v6w7x)

### Changed

- Configure ESLint with TypeScript-aware rules (y8z9a0b)
- Set up Prettier as code formatter (c1d2e3f)