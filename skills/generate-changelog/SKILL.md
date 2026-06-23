---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate changelog

Use this skill when a project needs a quick `CHANGELOG.md` from recent git history.

## Steps

1. Run `bash changelog.sh --stdout` to preview the generated changelog.
2. Run `bash changelog.sh` to write `CHANGELOG.md`.
3. Review the output and adjust wording only if the commit subjects need human cleanup.

## Behavior

The script reads commits since the latest git tag, skips merge commits, and groups entries into:

- Added
- Fixed
- Changed
- Removed

If the repository has no tags, it uses the full available git history.
