---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history categorized into Added, Fixed, Changed, and Removed.
---

# /generate-changelog Skill

Run this skill to inspect recent git commits since the last tag and generate or update the project's `CHANGELOG.md`.

## Instructions
1. Run `python3 skills/generate-changelog/generate_changelog.py` or `bash skills/generate-changelog/changelog.sh`.
2. The script parses commit messages formatted according to the Conventional Commits specification.
3. Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
4. Writes formatted release notes directly into `CHANGELOG.md`.
