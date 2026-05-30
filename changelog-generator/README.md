# Git Changelog Generator

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy this directory into any git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md`.

## Options

```bash
bash changelog.sh --dry-run
bash changelog.sh --output RELEASE_NOTES.md
bash changelog.sh --since v1.2.3
```

The generator categorizes commits into `Added`, `Fixed`, `Changed`, and
`Removed` using conventional commit prefixes and common action words.
