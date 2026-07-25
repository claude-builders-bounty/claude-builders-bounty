---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history since the last tag
trigger: /generate-changelog
---

# CHANGELOG Generator

Generates a structured `CHANGELOG.md` by analyzing git commits since the last tag.

## Usage

```
/generate-changelog
```

Or via CLI:

```bash
bash skills/changelog-generator/changelog.sh
bash skills/changelog-generator/changelog.sh --repo /path/to/repo --output CHANGELOG.md
```

## Behavior

- Fetches all commits since the most recent git tag
- Parses conventional commit prefixes (feat:, fix:, BREAKING CHANGE:, chore:, refactor:, docs:, test:, style:)
- Falls back to keyword detection (add, fix, change, remove, bump, merge) for non-conventional messages
- Auto-categorizes into: Added / Fixed / Changed / Removed / Internal
- Generates timestamped, well-formatted Markdown output
- Handles edge cases: no tags, no commits, empty repos, dirty working trees

## Output Sections

| Prefix | Section | Description |
|--------|---------|-------------|
| `feat:` | Added | New features |
| `fix:` | Fixed | Bug fixes |
| `BREAKING CHANGE:` | Changed | Breaking API changes |
| `refactor:` | Changed | Code restructuring |
| `perf:` | Changed | Performance improvements |
| `chore:`, `docs:`, `test:`, `style:`, `build:`, `ci:` | Internal | Maintenance tasks |

## Example

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

- Git 2.x
- Bash 4+
- Repository with at least one annotated or lightweight tag
