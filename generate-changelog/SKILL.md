---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, using commits since the latest git tag and grouping entries into Added, Fixed, Changed, and Removed.
---

# Generate Changelog

Use this skill when a repository needs a release changelog generated from git commit history.

## Workflow

1. Run `bash generate-changelog/changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md`.
3. Edit any entry that needs product wording before committing the changelog.

## Behavior

- Reads commits since the latest git tag.
- Falls back to full history when the repository has no tags.
- Groups commits into:
  - `Added`
  - `Fixed`
  - `Changed`
  - `Removed`
- Writes a Keep a Changelog-style `CHANGELOG.md`.
- Preserves existing changelog content below the new generated section.

## Command

```bash
bash generate-changelog/changelog.sh
```

Useful options:

```bash
bash generate-changelog/changelog.sh --dry-run
bash generate-changelog/changelog.sh --output RELEASE_NOTES.md
bash generate-changelog/changelog.sh --since v1.2.0
```

## Review Checklist

- Confirm the detected tag range is correct.
- Confirm each entry is user-facing enough for release notes.
- Move internal-only chores to `Changed` or remove them if they do not belong in public release notes.
