---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history since the latest tag.
---

# Generate Changelog

Use this skill when a repository needs a categorized `CHANGELOG.md` generated from recent git history.

## Instructions

1. Run `bash changelog/changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md`.
3. Edit section wording if the project uses custom release language.

The script categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`. It uses the latest reachable git tag as the starting point and falls back to the full git history when no tag exists.
