---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history.
---

# Generate Changelog

Use this skill when a project needs a `CHANGELOG.md` generated from recent commits.

## Command

```bash
bash changelog.sh
```

Optional output path:

```bash
bash changelog.sh docs/CHANGELOG.md
```

## What it does

1. Finds the latest git tag with `git describe --tags --abbrev=0`.
2. Reads non-merge commit subjects since that tag, or all history if there is no tag.
3. Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
4. Writes a formatted `CHANGELOG.md`.

## Categorization rules

- `feat:`, `feature:`, `add:` → Added
- `fix:`, `bugfix:`, `hotfix:` → Fixed
- `remove:`, `delete:`, `deprecate:` → Removed
- `change:`, `refactor:`, `perf:`, `docs:`, `test:`, `ci:`, `chore:` → Changed
- Unknown prefixes default to Changed
