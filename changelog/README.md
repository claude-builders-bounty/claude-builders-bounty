# Generate Changelog

Create a structured `CHANGELOG.md` from git commits since the latest tag.

## Install

```bash
chmod +x changelog/changelog.sh
./changelog/changelog.sh
```

## Output

The script writes `CHANGELOG.md` with Keep a Changelog-style sections:

- Added
- Fixed
- Changed
- Removed

Commits are read from the latest reachable git tag to `HEAD`. If no tag exists, the full git history is used.

## Sample Output

Generated from this repository:

```markdown
# Changelog

## Unreleased

### Added

- Add bounty issue examples and repository documentation

### Fixed

- No fixes detected.

### Changed

- Initial repository setup

### Removed

- No removals detected.
```
