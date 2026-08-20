# Sample CHANGELOG.md

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] (since v1.2.0) - 2026-08-20

### Added
- add user profile avatar upload API endpoint (3a8f1b2 by Samuel)
- support multi-tenant organization switching (9c4b1d0 by Samuel)

### Changed
- optimize database query execution plan for analytics (7e2a9c1 by Samuel)
- migrate middleware configuration to Next.js 15 conventions (4d1e8a3 by Samuel)

### Fixed
- resolve connection pool timeout under peak burst concurrency (b1a0e88 by Samuel)
- fix session cookie expiration mismatch on Safari (f9c32d1 by Samuel)

### Removed
- deprecate legacy v1 token endpoint (51d8b94 by Samuel)
