# Git Changelog Generator

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `changelog.sh` into the git repository you want to summarize.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md` and commit it with your release notes.

## What It Does

- Finds the latest git tag and collects commits after that tag.
- Falls back to the full commit history when no tag exists.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Supports common Conventional Commit prefixes such as `feat:`, `fix:`, `refactor:`, `docs:`, and `chore:`.

## Options

```bash
# Write to a custom file
CHANGELOG_FILE=RELEASE_NOTES.md bash changelog.sh

# Generate notes for a specific range
CHANGELOG_RANGE=v1.0.0..HEAD bash changelog.sh
```

## Sample Output

```markdown
# Changelog

## Unreleased

_Generated from commits since `v1.2.0`._

### Added

- Add CSV export for reports (`a1b2c3d`)

### Fixed

- Fix null response handling in API client (`d4e5f6a`)

### Changed

- Update onboarding copy (`789abcd`)

### Removed

- Remove legacy analytics endpoint (`012efab`)
```
