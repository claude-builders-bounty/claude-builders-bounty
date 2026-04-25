---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
triggers:
  - /generate-changelog
---

# Generate Changelog

Automatically generates a structured `CHANGELOG.md` from a project's git history,
categorizing commits into **Added**, **Fixed**, **Changed**, and **Removed** sections.

## Usage

Run one of the following commands:

```bash
# Generate changelog from last tag to HEAD
bash changelog.sh

# Generate from a specific tag
bash changelog.sh v1.2.0

# Generate full history across all tags
bash changelog.sh --all
```

Or invoke via Claude Code:

```
/generate-changelog
```

## How it works

1. Detects the latest git tag (or uses the one you specify).
2. Collects all non-merge commits in that range.
3. Classifies each commit based on its subject line prefix:
   - **Added** — add, create, introduce, implement, support, new
   - **Fixed** — fix, repair, resolve, correct, patch, bugfix, hotfix, close, handle
   - **Removed** — remove, delete, drop, eliminate, deprecate, strip
   - **Changed** — everything else
4. Writes a well-formatted `CHANGELOG.md` at the repo root.

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-04-25

### Added

- Add user authentication module (a1b2c3d)
- Implement dark mode toggle (e4f5g6h)

### Fixed

- Fix login redirect loop (i7j8k9l)
- Handle edge case in date parser (m0n1o2p)

### Changed

- Update dependency versions (q3r4s5t)
- Refactor database connection pool (u6v7w8x)

### Removed

- Remove deprecated legacy API endpoints (y9z0a1b)
```

## Files

- `changelog.sh` — The main bash script. Drop it in any git repo and run.
- `SKILL.md` — This file (Claude Code skill definition).
- `README.md` — Setup instructions.
