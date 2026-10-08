---
name: generate-changelog
description: Automatically generates a clean, categorized Keepachangelog CHANGELOG.md from git commits since the last tag.
---

# Git Structured Changelog Skill

Automatically inspects the local repository's git commit history since the most recent release tag, categorizes commits into standard sections (`Added`, `Fixed`, `Changed`, `Removed`), and updates `CHANGELOG.md`.

## Usage
Run directly from terminal or bash:
```bash
bash changelog.sh [version]
```
Or with python:
```bash
python generate_changelog.py v1.0.0
```

## How It Works
1. Identifies the latest git tag using `git describe --tags --abbrev=0`.
2. Extracts all commits between the tag and `HEAD`.
3. Auto-detects Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`, `revert:`, etc.).
4. Formats entries with short SHA references and writes to `CHANGELOG.md`.
