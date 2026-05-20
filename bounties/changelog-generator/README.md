# Changelog Generator

Generate a structured `CHANGELOG.md` from git history.

## Setup

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## What It Does

- Finds commits since the most recent git tag.
- Falls back to all commits if no tags exist.
- Groups commit messages into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep a Changelog-style Markdown file.
- Preserves older changelog content below the new generated section.

## Options

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md --version Unreleased
```

## Test

```bash
bash test_changelog.sh
```

See `sample-output.md` for output generated from a real GitHub repository.

