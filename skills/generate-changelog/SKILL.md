---
name: generate-changelog
description: Automatically generates a structured, Keep a Changelog compliant CHANGELOG.md from git history.
command: /generate-changelog
---

# Generate Changelog Skill

This skill analyzes git commits since the last tag (or initial commit) and creates/updates `CHANGELOG.md` categorized into `Added`, `Fixed`, `Changed`, and `Removed`.

## Instructions for Claude Code:
1. Run `python3 skills/generate-changelog/generate_changelog.py` in the workspace root.
2. Review the generated `CHANGELOG.md` file to ensure clean categorization.
3. Present the unreleased changelog summary to the user.
