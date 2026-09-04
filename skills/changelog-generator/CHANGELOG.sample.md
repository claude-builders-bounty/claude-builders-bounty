# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-09-04

### Added
- New user authentication with JWT tokens (a1b2c3d)
- OAuth2 provider support for GitHub and Google (e4f5g6h)
- Rate limiting middleware for API endpoints (i7j8k9l)

### Fixed
- Memory leak in background job processor (b2c3d4e)
- Race condition when concurrent orders are processed (f5g6h7i)
- Incorrect timezone handling in scheduled tasks (j8k9l0m)

### Changed
- Upgraded Express from 4.18 to 5.0 (n0p1q2r)
- Migrated raw SQL queries to use parameterized bindings (s3t4u5v)
- Improved error responses with request IDs for tracing (w6x7y8z)

### Removed
- Deprecated legacy REST API v1 endpoints (a9b0c1d)
- Unused jQuery dependency from admin panel (d2e3f4g)

---
*8 commit(s) by 3 contributor(s)*
