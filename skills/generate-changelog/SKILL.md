---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag, categorized into Added, Fixed, Changed, and Removed.
---

# /generate-changelog Skill

Run this skill to inspect recent git commits since the last tag and generate or update the project's `CHANGELOG.md`.

## Instructions
1. Run `bash skills/generate-changelog/changelog.sh` or `python3 skills/generate-changelog/generate_changelog.py`.
2. The script parses Conventional Commits (`feat:`, `fix:`, …) with a keyword fallback for plain messages.
3. Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`; merge commits are filtered out.
4. Writes the new section by prepending it to `CHANGELOG.md` (existing history is kept). Options: `--repo`, `--output`, `--tag`, `--since`.
