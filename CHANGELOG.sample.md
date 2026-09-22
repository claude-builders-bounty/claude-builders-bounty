# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - 2026-09-23 (since tag: v1.0.0)

### Added
- feat: add Google OAuth2 authentication flow (`a3f89b1`)
- feat(billing): integrate Stripe webhook listener for subscription renewals (`b8c12a4`)
- feat: support dark mode theme toggle across all dashboard views (`c912def`)

### Fixed
- fix: resolve intermittent race condition in session token refresh (`d409e51`)
- fix(ui): correct mobile viewport overflow on registration page (`e7182f3`)
- bugfix: handle null pointer exception when avatar image is missing (`f2201aa`)

### Changed
- refactor: optimize database connection pooling for PostgreSQL (`109ab34`)
- chore(deps): upgrade Next.js to v15.2.0 and React to v19 (`21a0cd5`)
- docs: update installation instructions and API reference in README (`32b1de6`)

### Removed
- remove: drop deprecated v1 REST API endpoints (`43c2ef7`)
- deprecate: remove legacy XML export format in favor of JSON/CSV (`54d3fa8`)
