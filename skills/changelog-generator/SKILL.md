---
name: changelog-generator
description: Automatically generate a structured CHANGELOG.md from git history. Categorizes commits into Added/Fixed/Changed/Removed since the last tag.
---

# changelog-generator

Generate a structured `CHANGELOG.md` from git history.

## Usage

```
/generate-changelog           # Generate from HEAD to last tag
/generate-changelog v1.0.0    # Generate from v1.0.0 to HEAD
/generate-changelog --since 2024-01-01 --to HEAD
```

Or standalone:
```bash
bash changelog.sh
bash changelog.sh --since v1.0.0 --to HEAD --output CHANGELOG.md
```

## Output

A clean, categorized changelog:
```markdown
# Changelog

## [Unreleased] — 2025-07-18

### Added
- New user dashboard with analytics charts (#42)
- Dark mode support across all pages (#38)

### Fixed
- Login redirect loop on expired sessions (#41)
- Memory leak in WebSocket connection (#39)

### Changed
- Upgrade React from 17 to 18 (#40)
- Increase API rate limit from 100 to 500 req/min

### Removed
- Deprecated v1 API endpoints
```
