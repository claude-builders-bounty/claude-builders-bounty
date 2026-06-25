---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a git repository history. Use when a user asks to create, refresh, or draft a changelog from commits, especially when the output should be categorized into Added, Fixed, Changed, and Removed sections.
---

# Generate Changelog

Use the bundled changelog generator when the user wants a deterministic changelog from git history.

## Workflow

1. Run `bash changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md`.
3. If needed, rerun with `--since <tag>` or `--output <path>`.

## Options

- `--repo <path>`: target repository, defaults to current directory.
- `--since <tag-or-ref>`: start from a specific tag/ref. If omitted, the script uses the latest git tag.
- `--stdout`: print the changelog instead of writing `CHANGELOG.md`.

Prefer the generated categories as a starting point and make small wording edits only when a commit subject is unclear.
