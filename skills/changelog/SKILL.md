---
name: changelog
description: Generate a structured CHANGELOG.md from git history since the last tag
---

# /generate-changelog

Generates a structured `CHANGELOG.md` by analyzing git history since the last tag.

## Usage

`/generate-changelog [--output FILE] [--tag TAG]`

**Options:**
- `--output FILE` — Output file path (default: `CHANGELOG.md`)
- `--tag TAG` — Starting tag (default: latest tag via `git describe --tags --abbrev=0`)

## How it works

1. Finds the last git tag or uses the provided `--tag`
2. Groups commits since that tag into categories:
   - **Added** — new features (`feat:`, `feature:`, `add`)
   - **Fixed** — bug fixes (`fix:`, `bugfix:`, `bug fix`)
   - **Changed** — refactors, updates, dependency bumps
   - **Removed** — removed features or files
3. Writes a formatted `CHANGELOG.md`

## Example output

```markdown
# Changelog

## [1.1.0] - 2025-06-01

### Added
- User authentication with JWT (#42)
- Dark mode toggle (#38)

### Fixed
- Crash on empty search results (#35)
- Email validation edge case (#31)

### Changed
- Upgraded Express to v5
- Refactored database layer
```

## Implementation

Relies on `git log --oneline` and conventional commit parsing.
