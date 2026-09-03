---
name: git-changelog-generator
description: Automatically generates a structured, categorized CHANGELOG.md from recent git commit history.
actions:
  - generate-changelog
---

# Git Changelog Generator Skill

This skill analyzes git commit history since the latest git tag and generates a categorized `CHANGELOG.md` adhering to the Keep a Changelog convention.

## Usage in Claude Code

Run the slash command:
```text
/generate-changelog
```

Or trigger via CLI:
```bash
python skills/git-changelog-generator/changelog.py
```
