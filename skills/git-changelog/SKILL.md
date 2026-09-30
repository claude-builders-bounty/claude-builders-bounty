---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history, categorized into Added, Fixed, Changed, and Removed.
---

# Git Changelog Generator Skill

Use this skill whenever you need to prepare release notes, update `CHANGELOG.md`, or review changes since the last git release tag.

## How to Run

Execute the script from the root of the project:

```bash
bash skills/git-changelog/changelog.sh [VERSION] [OUTPUT_FILE]
```

Parameters:
- `VERSION` (optional): Version label to assign (default: `Unreleased`, e.g. `v1.2.0`).
- `OUTPUT_FILE` (optional): Output markdown file (default: `CHANGELOG.md`).

## Categorization Rules
- **Added**: `feat:`, `feat(*):`, `add ...`
- **Fixed**: `fix:`, `fix(*):`, `bugfix:`
- **Removed**: `revert:`, `remove:`, `deprecated:`
- **Changed**: `refactor:`, `perf:`, `style:`, `chore:`, `docs:`, `test:`, `build:`
