---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, grouped into Added, Fixed, Changed, and Removed sections.
---

# Generate Changelog

Use this skill when a user asks to create or refresh a project `CHANGELOG.md` from git commits.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run `bash changelog.sh` to generate `CHANGELOG.md`, or pass a custom output path with `bash changelog.sh RELEASE_NOTES.md`.
3. Review the generated sections and adjust wording only when the commit subject is unclear.

## Behavior

- Uses the latest git tag as the starting point.
- Falls back to the full repository history when no tags exist.
- Ignores merge commits.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Includes short commit hashes for traceability.

