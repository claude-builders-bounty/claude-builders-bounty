---
name: generate-changelog
description: Generate a structured CHANGELOG.md from the current git repository history since the latest tag.
---

# Generate Changelog

Use this skill when the user wants a release changelog from git history.

## Steps

1. Run `./changelog.sh --stdout` to preview the generated changelog.
2. If the grouping looks right, run `./changelog.sh` to write `CHANGELOG.md`.
3. Review the file and adjust wording only when a commit subject is unclear.

## Behavior

- Uses the latest git tag as the starting point.
- Falls back to all history when the repository has no tags.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Ignores merge commits.
