# Changelog Generator

Generate a structured `CHANGELOG.md` from git history.

## Setup

1. Copy or keep `changelog.sh` in the repository you want to document.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md`.

## What It Does

- Finds commits since the most recent git tag.
- Falls back to all commits when the repository has no tags.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep a Changelog-style `CHANGELOG.md`.

## Options

```bash
OUTPUT=docs/CHANGELOG.md bash changelog-generator/changelog.sh
```

`OUTPUT` defaults to `CHANGELOG.md`.

## Test

```bash
bash changelog-generator/test_changelog.sh
```
