# Changelog Generator

Generate a structured `CHANGELOG.md` from git history.

## Setup And Usage

1. Copy `changelog.sh` into the root of any git repository.
2. Run `bash changelog.sh` to generate `CHANGELOG.md`.
3. Review the generated sections and commit the result.

## What It Does

- Finds the latest git tag.
- Reads non-merge commits from the latest tag to `HEAD`.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a formatted `CHANGELOG.md`.

If no git tag exists, the script uses the full git history.

## Optional Output Path

```bash
bash changelog.sh docs/CHANGELOG.md
```
