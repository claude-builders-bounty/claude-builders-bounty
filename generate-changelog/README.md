# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy this folder plus `changelog.sh` and `scripts/generate_changelog.py` into a git repository.
2. Run `bash changelog.sh` from the repository root.
3. Commit the generated `CHANGELOG.md`.

Useful options:

```bash
bash changelog.sh --version v1.2.3
bash changelog.sh --since v1.2.2 --output CHANGELOG.md
bash changelog.sh --stdout
```

The output is grouped into `Added`, `Fixed`, `Changed`, and `Removed`.
