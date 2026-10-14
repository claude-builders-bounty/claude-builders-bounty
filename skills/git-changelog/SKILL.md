---
name: generate-changelog
description: Generates a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog Skill

This skill categorizes commits into:
- `Added`: Commits starting with `feat:`, `add:`, or `feature:`
- `Fixed`: Commits starting with `fix:`, `bug:`, or `patch:`
- `Changed`: Commits starting with `change:`, `refactor:`, `perf:`, `update:`, or `style:`
- `Removed`: Commits starting with `remove:`, `deprecate:`, or `delete:`

## Execution
Run:
```bash
bash changelog.sh CHANGELOG.md
```
