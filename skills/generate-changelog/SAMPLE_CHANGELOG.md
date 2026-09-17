# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.2.0] - 2026-09-17 (since v1.1.0)

### Added
- Add OAuth2 Google and GitHub login providers (`a1b2c3d`)
- Implement real-time websocket status streaming (`e5f6g7h`)
- Create exportable analytics summary dashboard (`9876543`)

### Fixed
- Resolve memory leak during reconnect retry cycles (`3344556`)
- Handle edge case with null timestamps in session store (`7788990`)
- Fix pagination offset calculation when limit is 0 (`aabbccd`)

### Changed
- Optimize database connection pool acquire latency (`ddeeff1`)
- Update documentation and API client examples (`2233445`)
- Upgrade core dependencies to latest LTS versions (`6677889`)

### Removed
- Remove deprecated v1 legacy REST endpoints (`1122334`)
- Delete unused test fixtures and dead code (`889900a`)

---

## [v1.1.0] - 2026-08-15

### Added
- Initial release of task execution runner (`1029384`)
- Docker containerization support (`5647382`)
