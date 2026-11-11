# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v1.2.0] - 2026-11-11

### Added
- add automated changelog generator script (`changelog.sh`) ([a1b2c3d](a1b2c3d))
- add `/generate-changelog` Claude Code skill definition (`SKILL.md`) ([d4e5f6a](d4e5f6a))
- add support for custom release tag headers and date stamping ([b7c8d9e](b7c8d9e))

### Fixed
- resolve edge-case where repositories with zero tags exited with error ([f1a2b3c](f1a2b3c))
- handle double-quoted commit messages containing special characters ([e4d5c6b](e4d5c6b))

### Changed
- refactor commit categorization to use POSIX regex pattern matching ([c7b8a9f](c7b8a9f))
- update README with 3-step quickstart guide ([1a2b3c4](1a2b3c4))

### Removed
- deprecate legacy manual changelog template ([5d6e7f8](5d6e7f8))
