---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history. Auto-categorizes commits into Added, Fixed, Changed, and Removed. Works via /generate-changelog slash command or python3 generate_changelog.py
---

# Changelog Generator

Generate a structured `CHANGELOG.md` from git history with one command.

## Usage

### As a slash command

```
/generate-changelog
```

### As a CLI

```bash
python3 generate_changelog.py
```

This will:
1. Detect the latest git tag
2. Fetch all commits since that tag (or all history if no tag exists)
3. Categorize each commit into Added / Fixed / Changed / Removed
4. Write a Markdown file to `CHANGELOG.md`

## Options

```bash
# Generate from a specific tag
python3 generate_changelog.py --since v1.0.0

# Include all history (ignore tags)
python3 generate_changelog.py --all

# Custom output path
python3 generate_changelog.py --output HISTORY.md

# Custom version label
python3 generate_changelog.py --version "2.0.0"
```

## Conventional Commit Format

The script recognizes standard conventional commit prefixes:

| Prefix | Category |
|---|---|
| `feat:`, `add:`, `new:` | Added |
| `fix:`, `bug:`, `patch:` | Fixed |
| `refactor:`, `update:`, `perf:`, `docs:`, `chore:`, `test:` | Changed |
| `remove:`, `delete:`, `deprecate:`, `revert:` | Removed |

Commits with `!` after the type (e.g., `feat!:`) are flagged as **BREAKING** with a ⚠️ marker.

## Requirements

- Python 3.6+
- `git` in PATH
- Run from inside a git repository

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-06-03

### Added
- add `msg-value-loop` (#15050)
- add `controlled-delegatecall` (#15046)

### Fixed
- identify forked contracts in debug traces (#15048)

### Changed
- update `solar` to latest main (#15003)
```

See `sample-output.md` for a real-world example with the foundry-rs/foundry repo.
