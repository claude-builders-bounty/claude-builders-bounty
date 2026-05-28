---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when a project needs a changelog generated from recent git commits.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run `bash changelog.sh`.
3. Review `CHANGELOG.md` and summarize the generated Added, Fixed, Changed, and Removed sections.

The script reads commits since the latest git tag. If the repository has no tags, it uses all reachable commits.
