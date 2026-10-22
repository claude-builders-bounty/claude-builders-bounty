# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.2.0] - 2026-10-22

### Added
- **auth**: Add OAuth2 Google and GitHub login providers (`4f1b8a9`)
- **export**: Add CSV and Markdown export for analytical reports (`7d2e3f1`)
- **cli**: Support `/generate-changelog` slash command and `--write` flag (`9c4a5b6`)

### Changed
- **cache**: Migrate session store to Redis LRU caching for sub-millisecond lookups (`2e8b1a4`)
- **router**: Streamline middleware execution order and eliminate redundant auth checks (`5f6d7e8`)

### Fixed
- **db**: Prevent unhandled connection pool timeout during burst traffic (`3a9c1d2`)
- **parser**: Resolve null pointer exception when parsing malformed git commit headers (`8b7e6f5`)

### Removed
- **legacy**: Drop deprecated v1 XML endpoint routes (`1a2b3c4`)

### Security
- **session**: Enforce cryptographic regeneration of session tokens on privilege escalation (`6e5d4c3`)

### Maintenance & Chores
- **deps**: Bump core dependencies to latest stable releases (`9f8e7d6`)
- **ci**: Add GitHub Actions test matrix across Linux, macOS, and Windows (`2c3d4e5`)

---

## [v1.1.0] - 2026-09-15

### Added
- **core**: Initial public API release with rate-limiting middleware (`f1e2d3c`)
- **docs**: Comprehensive OpenAPI 3.1 specification and quickstart guide (`b4a5c6d`)

### Fixed
- **cors**: Allow configurable origin headers for trusted internal microservices (`e7f8a9b`)
