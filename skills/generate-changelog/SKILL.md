---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, grouped into Added, Fixed, Changed, and Removed sections since the latest git tag.
---

# Generate Changelog

Use this skill when a user asks to create or refresh a repository changelog from git commits.

## Workflow

1. Run `bash changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md` for commit grouping and wording.
3. If needed, rerun with `--since <tag-or-ref>` or `--output <path>`.

The script fetches commits since the latest git tag by default. If the repository has no tags, it uses all reachable commits.
