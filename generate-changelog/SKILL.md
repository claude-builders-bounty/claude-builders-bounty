---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when the user asks to create or refresh a project changelog from git history.

## Steps

1. From the repository root, run:

   ```bash
   bash generate-changelog/changelog.sh
   ```

2. Review the generated `CHANGELOG.md` sections:
   - `Added`
   - `Fixed`
   - `Changed`
   - `Removed`

3. Edit wording only if product names or user-facing descriptions need polish.

## Behavior

- Uses commits since the latest git tag when a tag exists.
- Uses all commits when no tags exist.
- Skips merge commits.
- Categorizes conventional commits and keyword-based subjects.
- Writes a complete `CHANGELOG.md` in Keep a Changelog-style sections.

## Custom output path

```bash
CHANGELOG_OUTPUT=/tmp/CHANGELOG.preview.md bash generate-changelog/changelog.sh
```
