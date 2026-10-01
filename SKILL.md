---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Use when the user asks for a changelog, release notes, or a summary of recent commits.
---

# Generate Changelog

Generate or refresh a structured `CHANGELOG.md` from the project's git history.

## Steps

1. Run `bash changelog.sh` in the repository root. Optional arguments:
   - `$1` — start tag (default: the most recent tag via `git describe --tags --abbrev=0`; falls back to all history if no tags exist)
   - `$2` — output file (default: `CHANGELOG.md`)
2. Read the generated file and verify the four sections (`Added` / `Fixed` / `Changed` / `Removed`) look correct.
3. Show the user a short summary: version/date header, counts per category, and the range used.

## Categorization rules

- `feat`, `add`, `support`, `implement` → **Added**
- `fix`, `bug`, `patch`, `hotfix`, `repair` → **Fixed**
- `remove`, `delete`, `drop`, `revert`, `deprecate` → **Removed**
- everything else → **Changed**

Matching is done on the lowercased commit subject prefix, so `Fixed: crash on startup` and `fix(parser): ...` both land in **Fixed**.

## Notes

- Merge commits are excluded (`--no-merges`).
- Each entry keeps its short hash so it can be linked back to the commit.
- The script is idempotent: it overwrites the output file each run.
