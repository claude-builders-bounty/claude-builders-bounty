---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag.
tags: [git, documentation, release]
---

# /generate-changelog

Generate a structured `CHANGELOG.md` from git history.

## What it does

1. Finds the latest git tag (`git describe --tags --abbrev=0`)
2. Collects all non-merge commits since that tag
3. Auto-categorizes commits into **Added**, **Fixed**, **Changed**, **Removed**
4. Outputs a properly formatted `CHANGELOG.md`

## Usage

```
/generate-changelog
```

Or from the command line:

```bash
bash changelog.sh
```

### Options

```bash
bash changelog.sh --output docs/CHANGELOG.md   # Custom output path
bash changelog.sh --tag v2.0.0                 # Start from a specific tag
```

## Categorization Rules

Commits are categorized by prefix:

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `new:`, `introduce:`, `create:` | **Added** |
| `fix:`, `bug:`, `resolve:`, `patch:`, `hotfix:` | **Fixed** |
| `remove:`, `drop:`, `delete:`, `deprecate:` | **Removed** |
| Everything else | **Changed** |

## Output Example

```markdown
# Changelog

## [v1.0.0 → HEAD] — 2026-05-19

### Added
- Dark mode support
- Export to PDF feature

### Fixed
- Login redirect loop on Safari
- Memory leak in websocket handler

### Changed
- Updated dependencies
- Refactored auth middleware

### Removed
- Legacy API v1 endpoints
```

## Requirements

- `git` installed
- At least one git tag in the repository (optional — works without tags too)
