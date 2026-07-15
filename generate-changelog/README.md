# CHANGELOG Generator

Automatically generate a structured CHANGELOG.md from your project's git history.

## Quick Setup (3 Steps)

1. **Copy the skill**: Place `generate-changelog/` into your project root
2. **Make executable**: `chmod +x generate-changelog/changelog.sh`
3. **Run it**: `bash generate-changelog/changelog.sh`

Or use the Claude Code skill: type `/generate-changelog` in any git repo.

## Features

- Tag-aware: generates from last git tag automatically
- Auto-categorizes: Added / Changed / Fixed / Removed
- Conventional commits support: feat:, fix:, chore:, etc.
- Keyword fallback matching
- Clean markdown output
- Works in any git repository

## Output Example

```markdown
# Changelog

## [Unreleased] - 2026-06-29

### Added
- Add user authentication (a1b2c3d4) - 2026-06-28

### Fixed
- Fix login redirect bug (e5f6g7h8) - 2026-06-27

### Changed
- Update dependencies (i9j0k1l2) - 2026-06-26
```
