---
name: generate-changelog
description: "Generate structured CHANGELOG.md from git history, auto-categorizing commits into Added/Fixed/Changed/Removed sections."
version: 1.0.0
author: haisui157
---

# Generate Changelog

Automatically generates a structured `CHANGELOG.md` from the project's git history.

## Usage

### As a standalone script
```bash
python3 changelog.py --output CHANGELOG.md
```

### With custom start point
```bash
python3 changelog.py --since v1.0.0
```

### In another repo
```bash
python3 changelog.py --repo /path/to/project
```

## How It Works

1. Fetches commits since the last git tag (or a custom `--since` point)
2. Parses [Conventional Commits](https://www.conventionalcommits.org/) format
3. Categorizes into: **Added**, **Fixed**, **Changed**, **Removed**, **Security**, **Dependencies**, **Documentation**, **Maintenance**
4. Detects breaking changes (marked with `!` in commit message)
5. Extracts PR references from commit messages
6. Outputs a clean, formatted `CHANGELOG.md`

## Commit Format

The tool recognizes commits in Conventional Commits format:

```
feat: add user authentication              → Added
fix: resolve login redirect loop           → Fixed
refactor!: restructure API layer           ⚠ Changed (breaking)
docs: update README                        → Documentation
chore: bump dependencies                   → Maintenance
```

Non-conventional commits default to **Changed**.
