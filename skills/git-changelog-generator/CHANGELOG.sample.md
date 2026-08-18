# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.0.0] - 2026-08-18

> Changes since `v0.9.0` (8 commits)

### Added
- Claude Code skill descriptor and slash command trigger `/generate-changelog` (`a1b2c3d`) - @angelTomo9
- Automated git commit parser supporting Conventional Commits (`f4e5d6c`) - @angelTomo9
- Standalone CLI runner with `--prepend` and `--version` options (`b7c8d9e`) - @angelTomo9

### Fixed
- Tag boundary detection when no tags exist in repository (`1a2b3c4`) - @angelTomo9
- Unicode encoding handling on multi-platform environments (`5d6e7f8`) - @angelTomo9

### Changed
- Refactored category mapping to prioritize explicit prefixes over substring matches (`9a8b7c6`) - @angelTomo9

### Security
- Sanitized command arguments against shell injection vulnerabilities (`3e2d1c0`) - @angelTomo9

### Documentation
- 3-step setup guide and CLI reference in README (`7f6e5d4`) - @angelTomo9
