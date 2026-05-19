# generate-changelog — Claude Code Skill

Generate a structured `CHANGELOG.md` from a project's git history.

## Usage

```bash
/generate-changelog
```

Or as a standalone script:

```bash
bash changelog.sh [--repo /path/to/repo] [--from-tag v1.0.0] [--output CHANGELOG.md] [--repo-url https://github.com/owner/repo]
```

## What it does

1. Detects the latest git tag (or uses `--from-tag`)
2. Fetches all commits between that tag and HEAD
3. Auto-categorizes commits into **Added** / **Fixed** / **Changed** / **Removed**
4. Outputs a properly formatted `CHANGELOG.md`

## Categorization rules

| Category | Commit prefixes / keywords |
|----------|---------------------------|
| **Added** | `feat:`, `add`, `create`, `introduce`, `implement`, `new` |
| **Fixed** | `fix:`, `bug`, `patch`, `repair`, `resolve`, `hotfix`, `revert` |
| **Changed** | `change`, `update`, `modify`, `refactor`, `rename`, `move`, `upgrade`, `bump`, `improve`, `enhance`, `optimize` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate`, `eliminate`, `strip` |

## Options

- `--repo` — Path to the git repository (default: current directory)
- `--from-tag` — Start from this tag instead of the latest tag
- `--output` — Output file path (default: `CHANGELOG.md`)
- `--repo-url` — Base URL for commit links (e.g. `https://github.com/owner/repo`)

## Example output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## Unreleased (changes since v2.1.0)

### Added

- feat: add dark mode toggle (a1b2c3d) — Alice, 2026-05-10

### Fixed

- fix: resolve login redirect loop (e4f5g6h) — Bob, 2026-05-09

### Changed

- update: bump dependencies to latest versions (i7j8k9l) — Carol, 2026-05-08

### Removed

- deprecate: remove legacy API v1 endpoints (m0n1o2p) — Dave, 2026-05-07
```
