# Generate Changelog

Generate a structured `CHANGELOG.md` from git history.

## Command

```bash
bash changelog.sh
```

## What it does

- Finds commits since the last git tag, or all history if no tag exists.
- Groups commit subjects into `Added`, `Fixed`, `Changed`, `Removed`.
- Writes a Keep-a-Changelog-style `CHANGELOG.md`.

## Setup: 3 steps

1. Copy `changelog.sh` into any git repo.
2. Run `bash changelog.sh`.
3. Review/commit the generated `CHANGELOG.md`.
