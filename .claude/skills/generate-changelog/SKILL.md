---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a git repository's history, categorizing commits since the last tag into Added / Fixed / Changed / Removed. Use whenever the user asks to create, update, or generate a changelog or release notes from git history (e.g. "/generate-changelog", "make a changelog", "release notes since last tag").
---

# Generate Changelog

Produce a [Keep a Changelog](https://keepachangelog.com/)-style `CHANGELOG.md`
from a project's git history, with commits auto-categorized into
**Added / Fixed / Changed / Removed**.

## When to use
Trigger on requests like: "generate a changelog", "create release notes",
"update CHANGELOG from git", or the slash command `/generate-changelog`.

## Fastest path
This skill ships a self-contained script. From the repository root run:

```bash
bash changelog.sh [REPO_DIR] [OUTPUT_FILE]
# REPO_DIR     git repo to read   (default: current directory)
# OUTPUT_FILE  changelog to write (default: <REPO_DIR>/CHANGELOG.md)
```

It writes `CHANGELOG.md` and also prints it to stdout.

## What it does (also the manual algorithm)
1. **Range** — commits since the most recent tag
   (`git describe --tags --abbrev=0`); if the repo has no tags, from the first commit.
2. **Categorize** each non-merge commit subject by Conventional-Commit prefix,
   with a keyword fallback:
   - `feat` / `feature` / `add` / "new …" → **Added**
   - `fix` / `bugfix` / `hotfix` / "resolve …" → **Fixed**
   - `remove` / `delete` / `revert` / `deprecate` / `drop` → **Removed**
   - everything else (`refactor`, `perf`, `docs`, `chore`, `style`, `update`, …) → **Changed**
3. **Write** a `## [<version>] - <date>` section containing the non-empty
   category sub-sections in Added / Changed / Fixed / Removed order.

## Output format
```markdown
# Changelog

## [v1.2.0] - 2026-07-09
_N change(s) since v1.1.0._

### Added
- feat: ...

### Changed
- refactor: ...

### Fixed
- fix: ...

### Removed
- remove: ...
```

## Notes
- Deterministic: no network, reads only local git history.
- Merge commits are skipped.
- Idempotent: re-running regenerates `CHANGELOG.md` for the current range.
