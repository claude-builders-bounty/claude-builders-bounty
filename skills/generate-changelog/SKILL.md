---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history. Use when the user asks to create, update, or regenerate a changelog, or invokes /generate-changelog.
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from the project's git history.

## When to use

- The user asks to create or update a `CHANGELOG.md`
- Before a release, to summarize changes since the last git tag

## How to run

Run the bundled script from the skill directory:

```bash
bash changelog.sh
```

Or invoke this skill directly: `/generate-changelog`

## Options

| Flag | Description |
|------|-------------|
| `-o, --output PATH` | Output file path (default: `CHANGELOG.md`) |
| `-s, --since TAG` | Start from a specific tag instead of auto-detecting |
| `--all` | Include the full history (ignore tags) |
| `--include-merges` | Include merge commits (excluded by default) |
| `-h, --help` | Show help |

## What it does

- Fetches commits since the last git tag (or all commits if no tags exist)
- Auto-categorizes commits into **Added** / **Fixed** / **Changed** / **Removed**
- Writes a properly formatted `CHANGELOG.md` in the project root

## Commit convention

For best results, use conventional commit prefixes (case-insensitive, scope and breaking-change `!` supported):

- `feat:`, `add:`, `new:`, `introduce:`, `implement:`, `support:`, `create:` → **Added**
- `fix:`, `bug:`, `bugfix:`, `hotfix:`, `patch:`, `correct:`, `resolve:`, `repair:` → **Fixed**
- `remove:`, `delete:`, `drop:`, `deprecate:` → **Removed**
- `refactor:`, `chore:`, `ci:`, `build:`, `style:`, `perf:`, `docs:`, `test:`, `update:`, `change:`, `improve:`, `bump:`, `migrate:`, `rename:`, `revert:`, `config:`, `security:` → **Changed**
- No recognized prefix → **Changed** (default)

## Output format

```markdown
# Changelog

## [Unreleased] (since v1.2.0)

### Added
- add search input (`abc1234`)

### Fixed
- fix crash on empty state (`def5678`)

### Changed
- refactor auth flow (`0129abc`)

### Removed
- remove legacy API (`345def0`)
```

## Requirements

- Git repository with commit history
- Bash 4+ (Git Bash on Windows works)