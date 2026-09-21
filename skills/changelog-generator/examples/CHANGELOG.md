# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [v1.2.0] - 2026-09-21

### Added
- Pre-tool-use security hook intercepting dangerous bash commands (`9bf898f`)
- Drizzle ORM schema definition with multi-tenancy support (`6d62664`)
- Automated verification tests for SQLite constraints (`3a41bf9`)

### Fixed
- SQL comment bypass vulnerability in regex analyzer (`8986067`)
- Connection pool deadlock when running concurrent migrations (`4f19aa2`)

### Changed
- Refactored session verification middleware to use NanoIDs (`11acde2`)
- Optimized WAL pragma checkpoints for read-heavy workloads (`55b7091`)

### Removed
- Deprecated legacy REST endpoint `/api/auth/token` (`e83910c`)

### Security
- Added automated sanitization for raw SQL table identifiers (`01bd9aa`)
