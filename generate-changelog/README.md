# Generate Changelog

Create a structured `CHANGELOG.md` from git history.

## Setup

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` and commit it.

The script reads commits since the latest git tag. If the repository has no tags, it uses the full history. Commits are grouped into `Added`, `Fixed`, `Changed`, and `Removed` using conventional commit prefixes and common subject keywords.

## Usage

```bash
bash changelog.sh
```

Write to a custom path:

```bash
bash changelog.sh docs/CHANGELOG.md
```

## Sample

See `SAMPLE_CHANGELOG.md` for output generated from a real GitHub repository.
