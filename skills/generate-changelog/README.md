# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from git history.

## Setup

1. Copy `changelog.sh` into a git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## What It Does

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- Reads non-merge commits since that tag, or all commits if no tag exists.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown changelog to `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
```

Write to a custom file:

```bash
bash changelog.sh RELEASE_NOTES.md
```
