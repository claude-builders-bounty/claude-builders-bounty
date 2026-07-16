---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history. Auto-categorizes commits (Added/Fixed/Changed/Removed) since the last tag. Use when the user types /generate-changelog or asks to "write a changelog", "update the changelog", or "summarize recent changes".
---

# Generate Changelog

Produce a categorized `CHANGELOG.md` from git history.

## When to use
- User runs `/generate-changelog`
- User asks to create/update a changelog or summarize what changed

## How to run

The repository ships a self-contained `changelog.sh` (no dependencies beyond
`git` and `bash`). Run it from the repo root:

```bash
bash changelog.sh            # writes ./CHANGELOG.md
bash changelog.sh docs/CHANGELOG.md  # custom path
```

## What it does
1. Detects the last git tag; ranges commits from `last-tag..HEAD` (or all commits if untagged).
2. Bumps the patch version for the new entry heading (e.g. `v1.2.3` -> `v1.2.4`).
3. Categorizes each commit by conventional-commit / keyword prefix:
   - **Added** — `feat`, `add`, `new`, `create`, `implement`
   - **Changed** — `refactor`, `update`, `change`, `improve`, `chore`, `perf`, `docs`
   - **Fixed** — `fix`, `bug`, `resolve`, `patch`
   - **Removed** — `remove`, `delete`, `drop`
4. Prepends a dated entry to the existing `CHANGELOG.md` (preserving history).

## Output format
```markdown
# Changelog

## v0.2.0 — 2026-07-16

### Added
- new GitHub Actions CI workflow

### Fixed
- fix crash on empty config

### Changed
- refactor parser into modules
```

## Notes
- Pure bash + git; no Python or external packages required.
- Safe to run repeatedly — it only adds a new versioned block on top.
- If there are no new commits since the last tag, it exits cleanly with a notice.
