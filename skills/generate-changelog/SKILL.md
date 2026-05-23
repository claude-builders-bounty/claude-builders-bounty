---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the most recent tag.
---

# Generate Changelog

Use this skill when a repository needs a release-ready changelog from git history.

## Workflow

1. Run `bash changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md`.
3. Edit any commit wording that needs human release-note polish.

## Categorization Rules

The script groups commits by subject:

- `feat`, `add`, `create`, `implement`, `introduce`, `support` -> `Added`
- `fix`, `bug`, `repair`, `resolve`, `correct`, `patch` -> `Fixed`
- `remove`, `delete`, `drop`, `deprecate` -> `Removed`
- Everything else -> `Changed`

If the repository has no git tags, the script uses the full git history.
