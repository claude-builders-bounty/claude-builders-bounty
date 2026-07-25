---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history since the last tag
trigger: /generate-changelog
---

# CHANGELOG Generator

Generates a structured `CHANGELOG.md` by analyzing git commits since the last tag.

## Usage

```bash
# In any git repo with tags:
/generate-changelog
# Or run directly:
bash /path/to/changelog.sh [--repo /path/to/repo] [--output CHANGELOG.md]
```

## Behavior

- Fetches all commits since the most recent git tag
- Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
- Handles conventional commits (`feat:`, `fix:`, `BREAKING CHANGE:`, `chore:`, `refactor:`)
- Falls back to keyword detection for non-conventional messages
- Outputs a clean, well-formatted `CHANGELOG.md`

## Conventions Used

| Conventional Commit | Changelog Section |
|--------------------|-------------------|
| `feat:`            | Added             |
| `fix:`             | Fixed             |
| `BREAKING CHANGE:` | Changed (noted as breaking) |
| `refactor:`        | Changed           |
| `chore:` / `docs:` / `test:` | (internal, included but labelled) |

## Example Output

```markdown
# Changelog

## [1.2.0] - 2026-07-25

### Added
- New OCR preprocessing pipeline (#42)
- Support for batch document upload (#38)

### Fixed
- Memory leak in PDF renderer (#40)
- Crash on empty form fields (#35)

### Changed
- Migrated from pytesseract to Tesseract.js v5 (#36)
- Upgraded Express from 4.x to 5.x

### Removed
- Deprecated v1 API endpoints
```

## Requirements

- Git (any version)
- Bash 4+
- A git repository with at least one tag
