# Git Changelog Generator

Generates a structured `CHANGELOG.md` from commits since the latest Git tag.

## Setup

1. Copy this folder into a Git project.
2. Run:

```bash
python generate_changelog.py --repo . --output CHANGELOG.md
```

## What It Does

- Finds the latest Git tag with `git describe --tags --abbrev=0`
- Uses all commits after that tag, or all commits if no tags exist
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`
- Writes a standard Markdown changelog

## Optional Bash Entry Point

If Bash is available, run:

```bash
bash changelog.sh
```

## Test

```bash
python -m unittest discover -s tests
```
