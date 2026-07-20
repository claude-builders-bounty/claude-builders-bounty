# Changelog

## [Unreleased] — 2026-07-20

> Changes since `v0.1.0`

### Added
- add rate limiting to all public routes (`8860e7d`)
- feat: implement /users endpoint with pagination (`c85cc77`)

### Fixed
- fix: correct SQL injection vulnerability in search (`20757e9`)

### Changed
- perf: optimise database query for user lookup (`48d7ed8`)
- chore: bump dependency versions (`a4c766a`)
- refactor: extract auth logic into separate module (`3fd50a8`)

### Removed
- remove: deprecated v1 API endpoints (`a5fc48a`)

