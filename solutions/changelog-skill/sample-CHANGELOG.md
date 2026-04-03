# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-04-03

### Added
- feat: add OAuth2 login support (`a1b2c3d`)
- feat(api): introduce rate limiting middleware (`e4f5a6b`)
- add: user profile picture upload (`7c8d9e0`)

### Fixed
- fix: resolve null pointer crash on startup (`f1a2b3c`)
- fix(auth): correct token expiry calculation (`d4e5f6a`)
- bug: handle empty response from payment gateway (`7b8c9d0`)

### Changed
- refactor: extract database connection into service layer (`e1f2a3b`)
- chore: update dependencies to latest versions (`c4d5e6f`)
- docs: improve API reference for `/users` endpoint (`7a8b9c0`)
- ci: add automated integration tests to pipeline (`d1e2f3a`)
- perf(search): optimise full-text search index (`b4c5d6e`)

### Removed
- remove: drop support for Node.js 14 (`f7a8b9c`)
- deprecate: legacy `/v1/auth` endpoint removed (`0d1e2f3`)

---

## [1.4.2] - 2026-03-15

### Fixed
- fix: prevent XSS in user-submitted content (`a9b0c1d`)
- fix(ui): correct button alignment on mobile (`2e3f4a5`)

### Changed
- chore: bump eslint to v9 (`b6c7d8e`)

---

## [1.4.1] - 2026-02-28

### Added
- feat: dark mode toggle in settings (`f9a0b1c`)

### Fixed
- fix: broken pagination on search results page (`2d3e4f5`)

### Removed
- deprecate: remove `GET /api/legacy/users` endpoint (`a6b7c8d`)
