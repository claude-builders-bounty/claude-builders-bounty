---
name: changelog-generator
description: Generate structured, categorized CHANGELOG.md from git history, auto-sorted into Added / Fixed / Changed / Removed sections since the last tag.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - git
        - bash
    emoji: "📋"
    homepage: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
    os:
      - darwin
      - linux
---

# Changelog Generator 📋

Generate a structured, categorized `CHANGELOG.md` from git history since the last release tag.

## Quick Start

```bash
# In any git repository with tags:
bash changelog.sh
# → creates/updates CHANGELOG.md
```

## `/generate-changelog` (Claude Code / OpenClaw)

When the user types `/generate-changelog` in a project:

1. Run `git describe --tags --abbrev=0 2>/dev/null || echo ""` to get last tag.
2. If no tag exists, use `git log --oneline --reverse | head -1 | cut -d' ' -f1` for initial commit hash.
3. Run the changelog script or equivalent logic:
   - Fetch commits since last tag: `git log <last-tag>..HEAD --pretty=format:"- %s (%h)" --no-merges`
   - For each commit, classify by conventional commit prefix:
     - `feat:` or `feature:` → **Added**
     - `fix:` or `bug:` → **Fixed**
     - `refactor:`, `perf:`, `style:`, `update:` → **Changed**
     - `remove:`, `delete:`, `deprecate:` → **Removed**
     - `docs:`, `test:`, `chore:`, `ci:`, `build:` → omit or put in **Other** section
   - When commit has no conventional prefix, use heuristics to categorize
4. Write output to `CHANGELOG.md`
5. If `CHANGELOG.md` already has an "Unreleased" section, replace its content with the new entries
6. If no `CHANGELOG.md` exists, create one with a "Unreleased" section header

## Behavior

- **Deterministic**: same repo, same tag range → same output
- **Idempotent**: re-running replaces the "Unreleased" section only (preserves released version history below)
- **No API key needed**: pure git + bash
- **Safe**: only writes `CHANGELOG.md`, never modifies other files

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New feature description (abc1234)

### Fixed
- Bug fix description (def5678)

### Changed
- Refactored module description (ghi9012)

### Removed
- Deprecated feature description (jkl3456)
```

## Fallback

If `git` is not available or the directory is not a git repository, output an error message:

> "⚠️ Not a git repository or git is not installed. Run this command inside a git project."
