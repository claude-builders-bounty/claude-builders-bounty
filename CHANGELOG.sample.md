# Sample output

This is real output produced by `bash changelog.sh` on a repository with
Conventional Commits history (commit hashes shortened for the sample).

# Changelog

All notable changes to this project are documented in this file.
Generated automatically from git history by `changelog.sh`.

## since v1.4.0 (2026-03-01)

### Added

- Add dark mode toggle to settings panel (f3a9c12)
- Add CSV export for reports (b7e2d40)
- Support pagination on the activity feed (91c4e88)

### Fixed

- Fix crash when uploading files larger than 10 MB (2d5f7a1)
- Fix broken link in the footer (e8a3b09)

### Changed

- Refactor auth middleware for readability (c6d1f34)
- Update dependency `express` to 4.19.2 (4b9a2c7)

### Removed

- Remove deprecated `/v1/api` endpoints (7f2e5d0)

Run `bash changelog.sh` in your own repo to generate the real thing.
