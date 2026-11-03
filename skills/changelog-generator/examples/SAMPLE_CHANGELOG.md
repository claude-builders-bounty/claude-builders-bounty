# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2026-11-04

### Added
- Pre-tool-use security hook intercepting destructive bash commands (`7b8c2d1`)
- Support for Turso and better-sqlite3 database drivers in project template (`4f9a0e2`)
- Structured JSON output option for CI pipelines (`1c3d5f7`)

### Fixed
- Unhandled null pointer when git describe returns empty string on initial commit (`a2e4b6c`)
- Timestamp timezone parsing inconsistency across macOS and Linux (`8f1d3e5`)
- Regex matching for multi-line SQL delete queries (`6a7b8c9`)

### Changed
- Refactor commit parser to streamline categorization performance (`3d5e7f1`)
- Update Claude model reference to claude-sonnet-4-20250514 (`9b0c2a4`)
- Clean up test fixtures and temporary directories automatically (`2e4f6a8`)

### Removed
- Deprecated legacy configuration format in v1.0 schema (`5a7b9c1`)
- Unused experimental shell wrappers (`1f3d5b7`)
