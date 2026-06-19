---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from the project's git history.

## Instructions

1. Run `bash changelog.sh` or `bash changelog.sh v1.0.0..v2.0.0` for a specific range
2. The script auto-categorizes commits into: Added / Fixed / Changed / Removed
3. Review the output and write it to `CHANGELOG.md`

## Commit Prefix Conventions

- `feat:`, `add:` → **Added**
- `fix:`, `bug:`, `hotfix:` → **Fixed**
- `update:`, `refactor:`, `change:` → **Changed**
- `remove:`, `delete:`, `drop:` → **Removed**

If no prefix is detected, the commit goes to **Changed**.
