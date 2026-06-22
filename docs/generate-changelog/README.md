# Generate Changelog

Create a structured `CHANGELOG.md` from git history with one command.

## Setup

1. Copy `changelog.sh` and `scripts/generate_changelog.py` into a git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## What It Does

- Finds commits since the latest git tag, or the full history when no tag exists.
- Categorizes entries into `Added`, `Fixed`, `Changed`, and `Removed`.
- Supports Conventional Commits and plain-English commit subjects.
- Writes a properly formatted Markdown changelog.

## Examples

```bash
bash changelog.sh
bash changelog.sh --repo ../my-project --output docs/CHANGELOG.md
bash changelog.sh --stdout --no-hashes
```

See `samples/claude-builders-bounty-changelog.md` for output generated from this repository.
