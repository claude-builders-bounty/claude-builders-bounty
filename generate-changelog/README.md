# Generate Changelog

Create a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `changelog.sh` into the root of the git repository you want to summarize.
2. Run `bash changelog.sh`.
3. Open `CHANGELOG.md` and use it as your release changelog.

## What It Does

- Fetches tags from `origin` when available.
- Uses commits since the latest reachable git tag, or the full history when no tags exist.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes GitHub commit links when the repository remote points to GitHub.

## Options

```bash
bash changelog.sh --output RELEASE_NOTES.md
bash changelog.sh --no-fetch
```

## Test

```bash
bash generate-changelog/test.sh
```
