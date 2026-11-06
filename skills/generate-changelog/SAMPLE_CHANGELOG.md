# Changelog

All notable changes to this project are documented in this file.
Generated automatically from git history (Changes since `v1.0.0`).

## [v1.1.0] - 2026-11-06

### Added
- add OAuth2 PKCE token refresh flow (`f0f1255` by @autonomous-builder)

### Fixed
- resolve stale middleware race condition on concurrent updates (`561744c` by @autonomous-builder)

### Changed
- optimize streaming IN clause lookup latency (`d3a3079` by @autonomous-builder)

### Removed
- drop deprecated v0 REST endpoints (`86cc321` by @autonomous-builder)

### Security
- patch CVE-2026-1042 in webhook signature verifier (`88d8156` by @autonomous-builder)
