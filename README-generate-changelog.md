# Generate Changelog

This repository includes `generate_changelog.py`, a small Python utility that creates a structured `CHANGELOG.md` from git history.

## Setup

1. Copy `generate_changelog.py` into any git repository.
2. Run `python generate_changelog.py`.
3. Review the generated `CHANGELOG.md` before committing it.

## Behavior

- Uses commits since the latest git tag when a tag exists.
- Falls back to all commits when the repository has no tags.
- Ignores merge commits.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes to `CHANGELOG.md` by default, or to a custom path when one is passed:

```bash
python generate_changelog.py docs/CHANGELOG.md
```

## Sample Output

Tested against this repository:

```markdown
# Changelog

## 2026-07-08

Generated from git history for all commits.

### Added

- feat: initial README with bounty board

### Fixed

- None

### Changed

- Initial commit

### Removed

- None
```
