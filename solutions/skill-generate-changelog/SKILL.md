---
name: generate-changelog
description: >-
  Generate a structured CHANGELOG.md from a project's git history. Fetches the
  commits since the last git tag and auto-categorizes them into Added / Fixed /
  Changed / Removed. Use when the user asks to "generate a changelog", "update
  CHANGELOG.md", "summarize commits since the last release", or runs
  /generate-changelog.
---

# Generate Changelog

Turn a repository's git history into a clean, categorized `CHANGELOG.md`.

## When to use

Trigger this skill whenever the user wants a changelog or release notes derived
from git — e.g. *"generate a changelog"*, *"what changed since the last tag?"*,
*"write release notes for this release"*, or the explicit `/generate-changelog`
command.

## Command

```
/generate-changelog            # since the most recent git tag
/generate-changelog v1.2.0     # from a specific tag
/generate-changelog v1.1.0..HEAD
```

## Steps

1. Make sure the current working directory is the target git repository
   (`git rev-parse --is-inside-work-tree`).
2. Run the bundled script:
   ```bash
   bash changelog.sh [<tag-or-range>]
   ```
   If `changelog.sh` is not in the repo, copy it from this skill's directory
   first:
   ```bash
   cp changelog.sh . && bash changelog.sh
   ```
3. Confirm the result and show the user the generated `CHANGELOG.md`
   (`cat CHANGELOG.md`).

## What it does

- Resolves the range with `git describe --tags --abbrev=0` → `<last-tag>..HEAD`
  (falls back to the full history when the repo has no tags).
- Categorizes each commit subject (case-insensitive prefix match):
  - `feat` / `add` / `new` / `implement` → **Added**
  - `fix` / `bug` / `patch` / `hotfix` / `repair` → **Fixed**
  - `remove` / `drop` / `delete` / `deprecate` → **Removed**
  - everything else → **Changed** (safe default; nothing is dropped)
- Skips merge commits and writes `CHANGELOG.md` to the repo root.

## Notes

- Dependency-free: needs only `bash` 4+ and `git`.
- Override the output path with `CHANGELOG_FILE=docs/CHANGES.md bash changelog.sh`.
- To keep prior entries, run it into a temp file and concatenate, or commit the
  file after each release.
