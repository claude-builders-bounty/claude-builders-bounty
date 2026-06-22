---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag.
---

# Generate Changelog

Use `/generate-changelog` or run the script from the repo root.

## Commands

```bash
python skills/generate-changelog/changelog.py
bash skills/generate-changelog/changelog.sh
```

## Rules

1. Find latest tag with `git describe --tags --abbrev=0`
2. List commits from tag to `HEAD` (full history if no tags)
3. Categorize conventional commits into Added / Fixed / Changed / Removed
4. Write Keep a Changelog-style `CHANGELOG.md`

## Setup (3 steps)

1. Copy this folder to `.claude/skills/generate-changelog/`
2. Ensure Python 3.10+ is available
3. Run `python changelog.py` from your git repository root
