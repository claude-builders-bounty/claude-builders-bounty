---
title: "Generate CHANGELOG from git history"
description: "Auto-generate a structured CHANGELOG.md from git commits. Categorizes commits into Added/Fixed/Changed/Removed."
command: "generate-changelog"
---

# Generate CHANGELOG

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

Run in any git repository:

```bash
python skills/changelog/changelog.py
```

Or specify output path and repo:

```bash
python skills/changelog/changelog.py --output CHANGELOG.md --repo /path/to/repo
```

## How it works

1. Detects the last git tag (falls back to first commit if no tags exist)
2. Fetches all commits since that tag
3. Categorizes each commit using conventional commit prefixes:
   - **Added** — feat:, add, new, create, implement
   - **Fixed** — fix:, hotfix, bugfix, patch
   - **Changed** — refactor:, perf:, update, chore:, docs:, etc.
   - **Removed** — remove, delete, deprecate, drop, revert
4. Outputs a formatted `CHANGELOG.md`
