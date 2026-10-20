---
name: generate-changelog
description: Automatically inspects git commits since the last tag, categorizes them into Added, Fixed, Changed, and Removed, and generates a standard Keep a Changelog markdown file.
---

# Git Changelog Generator Skill

This skill analyzes git repository history and compiles a structured `CHANGELOG.md`.

## When to use
- User asks to update the CHANGELOG.
- Preparing a new release or tag.
- Triggered via `/generate-changelog`.

## Instructions
1. Run `python3 generate_changelog.py` or `./changelog.sh`.
2. To specify a target version:
   ```bash
   python3 generate_changelog.py --version v1.2.0
   ```
3. To specify a starting tag:
   ```bash
   python3 generate_changelog.py --since v1.1.0 --version v1.2.0
   ```
4. Output is automatically formatted according to Keep a Changelog specifications.
