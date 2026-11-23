---
name: generate-changelog
description: Automatically generates a clean, categorized CHANGELOG.md from recent git commit history since the latest tag.
---

# Generate Changelog Skill

Use this skill when you want to produce a structured release CHANGELOG from git commit history.

## Trigger
- `/generate-changelog`
- `bash changelog.sh` or `python generate_changelog.py`

## Instructions
1. Run `python skills/generate-changelog/generate_changelog.py` from repository root.
2. The script extracts commits since the previous git tag.
3. Automatically classifies into standard sections:
   - `Added` (features, additions)
   - `Fixed` (bugfixes, patches)
   - `Changed` (refactors, dependencies, chores)
   - `Removed` (deprecated, deleted modules)
4. Saves directly to `CHANGELOG.md`.
