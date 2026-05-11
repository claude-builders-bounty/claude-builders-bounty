# Generate Changelog

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy `tools/generate-changelog/` into any git repository.
2. Run `bash tools/generate-changelog/changelog.sh`.
3. Review the generated `CHANGELOG.md` and commit it.

## Behavior

- Uses `git describe --tags --abbrev=0` to find the latest tag.
- Reads non-merge commits from `<latest-tag>..HEAD`; if the repo has no tags, it reads `HEAD`.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a clean Markdown changelog to `CHANGELOG.md`.

## Command

```bash
bash tools/generate-changelog/changelog.sh --repo . --output CHANGELOG.md
```

The script only needs Python 3 and Git.
