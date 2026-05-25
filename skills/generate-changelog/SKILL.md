---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, a release changelog,
or a categorized summary of git history.

## Workflow

1. Run `bash skills/generate-changelog/changelog.sh`.
2. Inspect the generated `CHANGELOG.md`.
3. If needed, lightly edit wording while preserving the generated categories:
   `Added`, `Fixed`, `Changed`, and `Removed`.

The script reads commits since the latest git tag. If the repository has no
tags, it uses all commits in the current branch.
