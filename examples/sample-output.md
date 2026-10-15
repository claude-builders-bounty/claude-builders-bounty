# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [v1.1.0] - 2026-10-15

### Added
- feat: add automatic tag detection fallback to root commit ([9a8b7c6])
- feat: support Claude Code /generate-changelog skill integration ([8b7c6d5])
- feat: add --stdout option for pipeline streaming ([7c6d5e4])

### Fixed
- fix: resolve boundary condition when no tags exist in repo ([6d5e4f3])
- fix: correctly handle commit messages with pipe characters ([5e4f3a2])

### Changed
- refactor: streamline conventional commit categorization regex ([4f3a2b1])
- docs: update 3-step setup instructions in README ([3a2b1c0])

### Removed
- chore: remove legacy python dependency in favor of pure bash ([2b1c0d9])
