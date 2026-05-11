---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the last tag, grouped into Added, Fixed, Changed, and Removed sections.
---

# Generate Changelog

Use this skill when the user asks for a changelog from git history.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run `bash changelog.sh` to write `CHANGELOG.md`, or pass a custom output path such as `bash changelog.sh RELEASE_NOTES.md`.
3. Review the generated sections and adjust commit categorization only if the user asks for editorial cleanup.

The script reads commits since the most recent git tag. If the repository has no tags, it uses the full git history.
