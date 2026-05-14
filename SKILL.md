---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history using the bundled changelog.sh script. Use when a user asks to create release notes or a changelog from commits since the latest git tag.
---

# Generate Changelog

Use `changelog.sh` from the repository root to create a categorized `CHANGELOG.md`.

## Workflow

1. Confirm the current directory is a git repository.
2. Run `bash changelog.sh` to write `CHANGELOG.md`, or pass a custom output path such as `bash changelog.sh RELEASE_NOTES.md`.
3. Review the generated sections and commit the result.

## Behavior

- Reads commits since the latest git tag.
- Falls back to all commits when no tag exists.
- Ignores merge commits.
- Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Supports conventional commit scopes such as `feat(auth): add OAuth login`.

## Validation

Run:

```bash
bash tests/test_changelog.sh
```
