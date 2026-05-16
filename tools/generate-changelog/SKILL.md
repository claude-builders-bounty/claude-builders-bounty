---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Auto-categorizes commits into Added/Fixed/Changed/Removed using Conventional Commits parsing.
version: 1.0.0
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from the project's git history.

## Trigger

User says "generate changelog", "create changelog", or invokes `/generate-changelog`.

## What it does

1. Finds the latest git tag
2. Collects all commits since that tag
3. Parses Conventional Commit prefixes (feat, fix, etc.) and auto-categorizes
4. Outputs a properly formatted `CHANGELOG.md`

## How to run

### Via bash (zero deps)

```bash
bash changelog.sh
```

### Via Python (cross-platform)

```bash
python generate_changelog.py --repo . --output CHANGELOG.md
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--repo` | `.` | Path to git repository |
| `--output` / `-o` | `CHANGELOG.md` | Output file path |
| `--since` | latest tag | Start from a specific git ref |

## Categories

| Commit prefix | CHANGELOG section |
|--------------|-------------------|
| `feat:`, `feature:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `refactor:`, `style:`, `perf:` | Changed |
| `revert:`, `remove:`, `deprecate:` | Removed |
| `docs:` | Documentation |
| `test:` | Testing |
| `ci:` | CI/CD |
| `build:` | Build |
| `chore:` | Maintenance |

Non-conventional commits are categorized by keyword analysis.

## Example output

```markdown
# Changelog

## [Unreleased]

### Added
- feat: add OAuth2 support (`abc1234`)

### Fixed
- fix: memory leak in parser (`def5678`)
```
