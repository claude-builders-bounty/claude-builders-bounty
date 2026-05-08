# Changelog Generator

Generate a structured `CHANGELOG.md` from git commits since the latest git tag.

## Setup

1. Copy `changelog.sh` and `scripts/generate_changelog.py` into the target repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## What It Does

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Uses all commits if the repository does not have tags.
- Auto-categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a formatted `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
```

Write to a custom path:

```bash
bash changelog.sh --output docs/CHANGELOG.md
```

Preview without writing:

```bash
bash changelog.sh --stdout
```

