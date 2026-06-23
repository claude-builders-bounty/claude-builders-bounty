---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history. Categorizes commits into Added/Fixed/Changed/Removed sections."
---

# Generate CHANGELOG

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

Run from the project root:

```bash
bash changelog.sh
```

Or invoke via `/generate-changelog` in Claude Code.

## What it does

- Fetches commits since the last git tag
- Auto-categorizes into:
  - **Added** ? new features
  - **Fixed** ? bug fixes
  - **Changed** ? refactors, updates
  - **Removed** ? deprecated features
- Formats a clean, readable CHANGELOG.md
