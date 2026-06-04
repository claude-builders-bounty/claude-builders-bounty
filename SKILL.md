# Generate Changelog

A Claude Code skill that generates a structured `CHANGELOG.md` from git history.

## Usage

Run via the `/generate-changelog` command or directly with:

```bash
bash changelog.sh [output_file]
```

- `output_file` defaults to `CHANGELOG.md` in the repository root.
- Fetches commits since the last git tag (or all commits if no tags exist).
- Auto-categorizes commits into **Added**, **Fixed**, **Changed**, **Removed**, and **Other** based on conventional commit prefixes.

## How it works

1. Finds the last git tag via `git describe --tags --abbrev=0`
2. Collects all commits in the range `last_tag..HEAD` (skipping merges)
3. Categorizes each commit message by prefix:
   - `feat`, `add`, `new`, `feature` → **Added**
   - `fix`, `bugfix`, `hotfix`, `patch` → **Fixed**
   - `refactor`, `update`, `chore`, `improve`, `docs`, `test`, `ci`, `build`, `style`, `perf` → **Changed**
   - `remove`, `delete`, `drop` → **Removed**
   - Everything else → **Other**
4. Writes a properly formatted Markdown changelog

## Example output

```markdown
# Changelog

## [Unreleased] — 2025-06-04 since v1.2.0

### Added
- feat: add user authentication module
- feat: implement dark mode toggle

### Fixed
- fix: resolve memory leak in worker pool
- fix: correct timezone handling in scheduler

### Changed
- refactor: simplify database connection logic
- docs: update API reference
- chore: bump dependencies
```

## Integration with Claude Code

To use as a Claude Code skill, add to your `.claude/commands/` directory:

```markdown
---
description: Generate a structured CHANGELOG.md from git history
---

!bash changelog.sh
```
