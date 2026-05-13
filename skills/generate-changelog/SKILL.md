---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag.
---

# Generate Changelog

Use this skill when a user asks for `/generate-changelog`, a release changelog, or a structured changelog from git history.

## Workflow

1. Confirm you are inside a git repository.
2. Run `bash skills/generate-changelog/changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` before committing it.

## Behavior

The script finds the latest git tag and collects commits after that tag. If the repository has no tags, it uses all commits. It sorts commit subjects into:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

The output follows Keep a Changelog style and writes a dated `Unreleased` section to `CHANGELOG.md`.

## Options

```bash
bash skills/generate-changelog/changelog.sh
bash skills/generate-changelog/changelog.sh --output RELEASE_NOTES.md
bash skills/generate-changelog/changelog.sh --version 1.2.0
bash skills/generate-changelog/changelog.sh --since v1.1.0
```
