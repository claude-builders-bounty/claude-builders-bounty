---
name: generate-changelog
description: Automatically extracts git commits since the last release tag and generates an opinionated, structured CHANGELOG.md categorized into Added, Fixed, Changed, and Removed.
---

# /generate-changelog Skill

This skill analyzes git commits and builds a structured `CHANGELOG.md` file.

## Execution
Run the embedded command:
```bash
python3 skills/generate-changelog/generate_changelog.py
```
or via the bash shortcut:
```bash
bash skills/generate-changelog/changelog.sh
```

## Features
- Fetches all commits since the latest git tag (or from root if untagged).
- Auto-parses Conventional Commits (`feat`, `fix`, `refactor`, `chore`, etc.).
- Groups entries into Keep-a-Changelog standard categories:
  - **Added**
  - **Fixed**
  - **Changed**
  - **Removed**
- Prepends new release entries while preserving historical changelogs.
