# Changelog

All notable changes to this project will be documented in this file.

## [v1.0.0] - 2026-10-01 (since tag `v0.9.0`)

### Added
- PreToolUse security hook blocking destructive bash commands ([`a1b2c3d`])
- Native Claude Code skill for structured changelog generation ([`e4f5a6b`])
- Opinionated CLAUDE.md template for Next.js 15 App Router + SQLite ([`c9d0e1f`])

### Fixed
- Stdin JSON parsing regression under non-TTY shell execution ([`7c8d9e0`])
- Regular expression edge case for hyphenated bash flags ([`3b4c5d6`])

### Changed
- Refactor audit logging to use standard ISO UTC timestamps ([`f1e2d3c`])
- Optimize database connection pragmas for WAL mode concurrency ([`8a9b0c1`])

### Removed
- Deprecated legacy shell scripts in favor of native Python hook ([`4d5e6f7`])
