# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup in 3 steps

1. Copy `changelog.sh` into the root of any git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md` and commit it.

## Optional usage

Write to a custom path:

```bash
bash changelog.sh docs/CHANGELOG.md
```

## Sample output

```markdown
# Changelog

## Unreleased - 2026-05-20

_Generated from commits since v1.0.0._

### Added
- add login page (a1b2c3d)

### Fixed
- handle missing config file (d4e5f6a)

### Changed
- update README instructions (abc1234)

### Removed
- delete deprecated helper (def5678)
```

## Notes

The script uses conventional commit prefixes when available, but also falls back to simple keyword matching for plain-English commit subjects.
