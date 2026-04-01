---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, auto-categorizing commits into Added/Fixed/Changed/Removed sections.
command: /generate-changelog
---

# /generate-changelog

Generate a structured `CHANGELOG.md` from the project's git history.

## What it does

1. Finds the last git tag (or uses all commits if no tags exist)
2. Reads all commits since that tag
3. Auto-categorizes each commit into:
   - **Added** — new features (feat, add, new, create, implement, introduce, support)
   - **Fixed** — bug fixes (fix, bug, patch, resolve, repair, hotfix)
   - **Changed** — updates (refactor, change, update, improve, enhance, optimize, chore, ci, docs, test)
   - **Removed** — deletions (remove, delete, deprecate, drop)
4. Outputs a properly formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com)

## Usage

```
/generate-changelog                  # Since last tag
/generate-changelog --since v1.2.0   # Since specific tag
/generate-changelog --output CHANGES # Custom output file
```

## Implementation

Run the `changelog.sh` script in the project root:

```bash
bash changelog.sh
```

Or with options:

```bash
bash changelog.sh --since v1.0.0 --output CHANGELOG.md
```

## Output format

```markdown
# Changelog

## [Unreleased (since v1.2.0)] — 2026-04-01

### Added
- feat: add user authentication (`a1b2c3d`)

### Fixed
- fix: resolve memory leak in parser (`d4e5f6g`)

### Changed
- refactor: simplify database queries (`h7i8j9k`)

### Removed
- remove: deprecated API v1 endpoints (`l0m1n2o`)
```
