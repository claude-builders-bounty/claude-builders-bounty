---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when a user asks to create or refresh a `CHANGELOG.md` from git history.

## Usage

Run the bundled script from the repository root:

```bash
bash generate-changelog/changelog.sh
```

The script:

- Detects the latest git tag.
- Reads commits since that tag, or all commits when no tag exists.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep a Changelog-style `CHANGELOG.md`.

## Options

```bash
bash generate-changelog/changelog.sh --output CHANGELOG.md
bash generate-changelog/changelog.sh --from v1.2.3 --version 1.3.0
bash generate-changelog/changelog.sh --dry-run
```

## Notes

- Conventional Commit prefixes are used when present.
- Non-conventional commits are placed under `Changed`.
- Merge commits are skipped.
