---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history with auto-categorization (Added/Fixed/Changed/Removed). Run with `/generate-changelog`.
version: 1.0.0
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from a project's git history, automatically categorizing commits into Added / Fixed / Changed / Removed sections.

## Trigger

User says: "generate changelog", "create changelog", "changelog", or runs `/generate-changelog`.

## What it does

1. Detects the latest two git tags to determine the commit range
2. Scans all commits between those tags
3. Categorizes each commit by conventional commit prefix:
   - `feat:` / `feat!:` → **Added**
   - `fix:` → **Fixed**
   - `refactor:`, `perf:` → **Changed**
   - `revert:` → **Removed**
   - `chore:`, `docs:`, `style:`, `test:`, `ci:`, `build:` → **Changed**
   - Everything else → **Changed** (uncategorized)
4. Generates a well-formatted `CHANGELOG.md` with compare links

## Usage

```bash
# Generate changelog between last two tags
bash submissions/generate-changelog/generate-changelog.sh

# Generate since a specific tag
bash submissions/generate-changelog/generate-changelog.sh --since v1.0.0

# With GitHub compare links
REPO_URL=https://github.com/user/repo bash submissions/generate-changelog/generate-changelog.sh

# Custom output path
bash submissions/generate-changelog/generate-changelog.sh --output ../docs/CHANGELOG.md
```

## Requirements

- `git` installed
- Run from within a git repository
- Tags should follow semver conventions (v1.0.0, v2.1.0, etc.) for best results

## Output Format

```markdown
# Changelog

## [2.1.0] - 2026-05-24

[Full changelog](https://github.com/user/repo/compare/v2.0.0...v2.1.0)

### Added

- feat: add user authentication system (a1b2c3d)
- feat: implement dark mode toggle (e4f5g6h)

### Fixed

- fix: resolve race condition in task queue (i7j8k9l)
- fix: correct date formatting for UTC offset (m0n1o2p)

### Changed

- refactor: extract shared validation logic (q3r4s5t)
- chore: update dependencies to latest (u6v7w8x)

### Removed

- revert: remove deprecated legacy API endpoint (y9z0a1b)
```
