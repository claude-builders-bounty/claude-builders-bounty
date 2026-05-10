---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Auto-categorizes commits into Added/Fixed/Changed/Removed. Supports tag-aware, append mode, and conventional commits.
---

# Generate Changelog Skill

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Activation

Tell Claude Code:
```
/generate-changelog
```
Or:
```
/generate-changelog --from v1.0.0 --to v2.0.0
```

## What It Does

1. **Detects git tags** — finds the latest tag or uses `--from`/`--to` arguments
2. **Fetches commits** — reads all commits between the specified range
3. **Auto-categorizes** — sorts commits into `Added`, `Fixed`, `Changed`, `Removed` based on:
   - Conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `chore:`, `breaking:`, etc.)
   - Keyword detection in commit messages (`add`, `fix`, `remove`, `update`, `break`, etc.)
   - Scope extraction from conventional commits (`feat(auth):` → scope: `auth`)
4. **Formats output** — generates a clean `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com) format
5. **Append mode** — if `CHANGELOG.md` already exists, prepends new entries (preserving history)

## Categorization Rules

| Prefix/Keyword | Category |
|---|---|
| `feat:`, `add`, `new`, `create`, `introduce`, `implement`, `support` | **Added** |
| `fix:`, `fix`, `bug`, `patch`, `resolve`, `repair`, `correct`, `crash`, `error` | **Fixed** |
| `refactor:`, `change`, `update`, `modify`, `improve`, `enhance`, `migrate`, `move`, `rename`, `bump`, `upgrade` | **Changed** |
| `breaking:`, `BREAKING CHANGE` | **Changed** (with ⚠️ marker) |
| `remove:`, `remove`, `delete`, `drop`, `deprecate`, `eliminate`, `strip` | **Removed** |
| `chore:`, `docs:`, `test:`, `ci:`, `build:`, `style:` | **Skipped** (internal only) |

## Options

- `--from <tag>` — start tag (default: latest tag before HEAD)
- `--to <tag>` — end tag (default: HEAD)
- `--output <path>` — output file path (default: `CHANGELOG.md`)
- `--append` — prepend to existing CHANGELOG.md instead of overwriting
- `--all` — include `chore`/`docs`/`test` commits under a "Maintenance" section
- `--scope` — group entries by scope (e.g., `auth`, `api`, `ui`)

## Implementation

This skill delegates to `generate-changelog/generate_changelog.py`:

```bash
python3 generate-changelog/generate_changelog.py [--from TAG] [--to TAG] [--output PATH] [--append] [--all] [--scope]
```

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-05-10

### Added
- Support for multi-region deployments (#42)
- New CLI command `config export` (#38)

### Fixed
- Crash on startup when config file is missing (#45)
- Memory leak in long-running sessions (#40)

### Changed
- ⚠️ **BREAKING**: `api.authenticate()` now requires `token` parameter (#44)
- Upgraded dependency `requests` from 2.28 to 2.31 (#41)

### Removed
- Deprecated `v1_compat` module (#39)
```

## Notes

- Requires `git` to be available in PATH
- Requires Python 3.7+
- Works on Windows, macOS, and Linux
