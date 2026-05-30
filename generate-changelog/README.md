# Generate Changelog

Create a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `generate-changelog/changelog.sh` into the root of any git repository.
2. Run `bash changelog.sh` or `bash changelog.sh --include-hashes`.
3. Review the generated `CHANGELOG.md` and commit it.

## What It Does

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- Reads non-merge commits from that tag to `HEAD`.
- Categorizes entries into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown changelog with an `Unreleased` section.

## Options

```bash
bash changelog.sh --output CHANGELOG.md
bash changelog.sh --since v1.2.3
bash changelog.sh --include-hashes
```

If a repository has no tags, the script falls back to all history.
