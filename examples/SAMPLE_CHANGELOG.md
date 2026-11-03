# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.2.0] - 2026-11-03

### Added
- feat: add automated git history CHANGELOG generator skill (`a1b2c3d`)
- feat: support custom output path and tag discovery (`e4f5g6h`)

### Fixed
- fix: resolve tag regex fallback when no tags exist on branch (`7890abc`)
- fix: handle merge commit subjects with pipe delimiters cleanly (`def1234`)

### Changed
- refactor: optimize git log subprocess invocation with UTF-8 decoding (`56789ab`)

### Documentation
- docs: add 3-step setup guide and conventional commit mapping table (`cdef012`)
