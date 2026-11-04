# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-11-04
*Changes since tag `v1.2.0`*

### Added
- `a1b2c3d` feat(auth): implement OIDC session refresher and token exchange
- `e4f5g6h` feat(export): add CSV and JSON bulk export options

### Fixed
- `i7j8k9l` fix(api): resolve race condition in concurrent webhook dispatch
- `m0n1o2p` fix(ui): prevent layout shift on mobile navbar collapse

### Changed
- `q3r4s5t` refactor(db): migrate connection pool to async pg driver
- `u6v7w8x` chore(deps): upgrade dependencies to patch security vulnerabilities

### Removed
- `y9z0a1b` remove: deprecate legacy v1 token endpoint
