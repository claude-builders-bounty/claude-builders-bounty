---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
command: /generate-changelog
---

# Generate Changelog Skill

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## What it does

1. Fetches all commits since the last git tag (or from the beginning if no tags exist)
2. Auto-categorizes commits into: **Added**, **Fixed**, **Changed**, **Removed**
3. Outputs a properly formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) conventions

## How to use

Run the bash script directly:

```bash
bash skills/generate-changelog/changelog.sh
```

Or use the Claude Code skill command:

```
/generate-changelog
```

## Categorization rules

| Prefix / Keyword          | Category  |
|---------------------------|-----------|
| `feat:`, `add`, `new`    | Added     |
| `fix:`, `bug`, `patch`   | Fixed     |
| `change`, `update`, `refactor`, `move`, `rename` | Changed |
| `remove`, `delete`, `deprecate`, `drop` | Removed  |
| Everything else           | Changed   |

## Options

```bash
# Generate changelog since a specific tag
bash skills/generate-changelog/changelog.sh v1.2.0

# Generate changelog for all history
bash skills/generate-changelog/changelog.sh --all

# Preview without writing to file
bash skills/generate-changelog/changelog.sh --dry-run
```

## Output format

```markdown
# Changelog

## [Unreleased]

### Added
- feat: add user authentication endpoint (#42)

### Fixed
- fix: correct timezone offset in scheduler (#39)

### Changed
- refactor: simplify database connection pool (#38)

### Removed
- remove: deprecated v1 API routes (#35)
```
