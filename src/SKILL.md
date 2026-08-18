---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history categorized into Added, Fixed, Changed, and Removed.
---

# Generate Changelog Skill

This skill inspects git history since the last git tag (or recent commits) and formats a standard Keep-A-Changelog Markdown document.

## Commands
- `/generate-changelog`: Runs `python src/changelog.py CHANGELOG.md` to update project changelog.
