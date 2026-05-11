---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history.
---

# Generate Changelog

Use this skill when a user asks to generate or refresh a project changelog from git commits.

## Workflow

1. Run `bash changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md` sections: `Added`, `Fixed`, `Changed`, and `Removed`.
3. Adjust commit messages only if the source history contains unclear wording.

## Behavior

- Uses commits since the latest git tag by default.
- Supports `CHANGELOG_RANGE=<range> bash changelog.sh` for an explicit git range.
- Writes a Markdown changelog with commit links when the origin remote is on GitHub.
