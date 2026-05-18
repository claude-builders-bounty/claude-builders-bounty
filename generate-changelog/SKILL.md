---
name: generate-changelog
description: Generate a structured CHANGELOG.md from commits since the latest git tag.
---

# Generate Changelog

Use this skill when a user asks to generate, refresh, or draft a project changelog from git history.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run `bash generate-changelog/changelog.sh` from this package, or copy `changelog.sh` into the target repository and run `bash changelog.sh`.
3. Review `CHANGELOG.md` and adjust category wording only if the project has stricter release-note conventions.

## Output

The script fetches tags, finds the latest git tag, reads non-merge commits since that tag, and writes a Markdown changelog grouped into `Added`, `Fixed`, `Changed`, and `Removed`.
