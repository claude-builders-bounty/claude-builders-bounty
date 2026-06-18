Resolves #1

## What

A Claude Code skill (`SKILL.md` + `changelog.sh`) that auto-generates a structured `CHANGELOG.md` from git history. Categorizes commits into **Added / Fixed / Changed / Removed** based on conventional commit prefixes.

## How to use

Two ways:

1. Slash command in Claude Code: `/generate-changelog`
2. From shell: `bash changelog.sh [output_file]`

Output defaults to `CHANGELOG.md` in the current directory.

## What it does

- Fetches commits since the last git tag (or all commits if no tags exist)
- Auto-categorizes each commit:
  - `feat:` → **Added**
  - `fix:` → **Fixed**
  - `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `chore:`, `build:`, `ci:` → **Changed**
  - `BREAKING:`, `revert:`, subject contains "Remove" or "Delete" → **Removed**
  - Anything else → **Changed** (fallback)
- Writes a properly formatted Markdown section with subheadings per category

## Files

- `skills/changelog/SKILL.md` — Claude Code skill definition
- `skills/changelog/changelog.sh` — bash script (no Python / Node dependency, pure shell)
- `skills/changelog/README.md` — install + sample output

## Sample output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0 - 2026-06-18]

### Added

- User profile page with avatar upload
- Dark mode toggle in settings

### Fixed

- Login redirect loop on Safari
- Memory leak in image cache

### Changed

- Upgraded React to 18.3
- Refactored authentication module

### Removed

- Deprecated v1 API endpoints
```

## Installation (3 steps)

```bash
mkdir -p ~/.claude/skills/changelog
cp changelog.sh ~/.claude/skills/changelog/
cp SKILL.md ~/.claude/skills/changelog/
chmod +x ~/.claude/skills/changelog/changelog.sh
```

The skill auto-loads from `~/.claude/skills/changelog/SKILL.md` in Claude Code.

## Requirements

- `git` on PATH
- `bash` 4+ (uses `case` glob and `mktemp -d`)
- **No other dependencies** — pure shell, no Python, no Node, no jq

## Tested on

This PR was developed and verified on `wang282913946/claude-builders-bounty` (this very repo). The script processes the commit history of this PR's branch and produces a valid `CHANGELOG.md` with the expected categories.

## Bounty

$50 via Opire
