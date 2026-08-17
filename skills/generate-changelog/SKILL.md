---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# Generate Changelog

Generates a structured `CHANGELOG.md` from the project's git history, categorized
into **Added / Fixed / Changed / Removed** using conventional-commit prefixes.

## Usage

- Command: `/generate-changelog`
- Or run directly: `bash changelog.sh`

## What it does

1. Determines the commit range: everything since the **last git tag**
   (`git describe --tags --abbrev=0`), or the full history if no tags exist.
2. Reads commits with `git log --no-merges --format="%h|%s"`.
3. Auto-categorizes each commit by conventional-commit prefix:
   - `fix:`, `bugfix:`, `hotfix:` → **Fixed**
   - `feat:`, `feature:`, `add:`, `new:` → **Added**
   - `refactor:`, `perf:`, `chore:`, `build:`, `docs:`, `test:`, `style:` → **Changed**
   - `remove:`, `delete:`, `deprecate:` → **Removed**
   - Anything else → **Changed**
4. Writes a properly formatted `CHANGELOG.md` with commit hashes.

## Options

```bash
bash changelog.sh                # since last tag
bash changelog.sh v1.2.0         # since a specific ref/tag
bash changelog.sh --since HEAD~10
bash changelog.sh --output CHANGES.md
```

## Sample output

```markdown
# Changelog

Generated from `git log` since `v1.0.0` on 2026-08-17.

## Added
  - feat: add user profile page (`a1b2c3d`)
  - feat: implement dark mode (`e4f5a6b`)

## Fixed
  - fix: resolve login redirect loop (`c7d8e9f`)

## Changed
  - refactor: extract auth middleware (`b0c1d2e`)

## Removed
  - remove: drop legacy API v1 (`f1a2b3c`)
```
