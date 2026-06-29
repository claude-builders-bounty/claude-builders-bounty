# Generate Changelog

A zero-dependency bash generator that creates a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup in 3 Steps

1. Copy `changelog.sh` and the `generate-changelog/` folder into the root of any git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md`, then commit it with your release changes.

## What It Does

- Finds the most recent git tag and reads commits from that tag to `HEAD`.
- Falls back to the full git history when the repository has no tags.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a properly formatted Markdown changelog.
- Supports `--output`, `--range`, and `--include-authors` for release workflows.

## Examples

```bash
bash changelog.sh
bash changelog.sh --output docs/CHANGELOG.md
bash changelog.sh --range v1.0.0..HEAD --include-authors
```

The native Claude Code skill definition is available in `generate-changelog/SKILL.md`.
