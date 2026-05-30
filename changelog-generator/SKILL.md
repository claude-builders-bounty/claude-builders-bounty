---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when the user asks to create or update a changelog from a
repository's git history.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run `bash changelog-generator/changelog.sh --dry-run` to preview changes.
3. Run `bash changelog-generator/changelog.sh` to write `CHANGELOG.md`.

The script automatically finds the latest git tag, reads non-merge commits after
that tag, groups them into `Added`, `Fixed`, `Changed`, and `Removed`, and writes
a Markdown changelog with commit links when the origin remote is on GitHub.

## Useful Options

- `--since <tag-or-revision>`: override the starting point.
- `--output <path>`: write somewhere other than `CHANGELOG.md`.
- `--include-merges`: include merge commits.
- `--dry-run`: print without writing.
