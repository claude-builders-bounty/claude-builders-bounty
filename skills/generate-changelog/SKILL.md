---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history. Use when the user asks for release notes, a changelog, or a summary of commits since the latest tag.
---

# Generate Changelog

Use the bundled `changelog.sh` script to produce changelog content from git history.

## Workflow

1. Confirm the current directory is inside the target git repository.
2. Run `bash changelog.sh` to write `CHANGELOG.md`, or `bash changelog.sh --dry-run` to preview.
3. Review the generated sections before committing the file.

## Behavior

- Uses the latest reachable git tag as the start point.
- Falls back to all commits when the repository has no tags.
- Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Excludes merge commits by default; pass `--include-merges` when merge commits should appear.
