# Changelog Generator

Auto-generate a structured `CHANGELOG.md` from git history.

## Setup

1. Save `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh`

Or use as a Claude Code skill: `/generate-changelog`

## Sample Output

Using this repo's own commits:
```
# Changelog

## [1.0.0] - 2026-05-30

### Added
- feat: add changelog generator with categorized sections
- feat: add README with setup instructions

### Fixed
- fix: handle repositories with no tags gracefully
- fix: preserve commit order within categories

### Changed
- refactor: simplify commit categorization logic
- chore: bump conventional-commit patterns
```
