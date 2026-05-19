# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup and usage

1. Run `bash scripts/generate_changelog.sh` from the repository root.
2. Optionally pass a range: `bash scripts/generate_changelog.sh v1.0.0 HEAD`.
3. Commit the generated `CHANGELOG.md` after reviewing the output.

The script categorizes conventional commit subjects into `Added`, `Fixed`, `Changed`, and `Removed` sections. If no tag exists, it uses the first commit as the starting point.

## Sample output

```md
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-05-19

### Added
- add changelog generation script for bounty #1

### Fixed
- No fixes found.

### Changed
- No changed items found.

### Removed
- No removed items found.
```
