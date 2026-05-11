---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

Use this skill when the user asks to create, refresh, or summarize a project changelog from git history.

## Workflow

1. Run `bash changelog.sh --repo <project-root>` from this repository or copy `changelog.sh` plus `skills/generate-changelog/generate_changelog.py` into the target project.
2. Review the generated `CHANGELOG.md` and adjust any category that needs maintainer judgment.
3. Commit the changelog with the related release work.

## Behavior

- Reads commits since the latest git tag with `git describe --tags --abbrev=0`.
- Falls back to all commits when the repository has no tags.
- Groups changes into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown `CHANGELOG.md` by default.
