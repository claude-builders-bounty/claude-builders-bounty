# Generate a Structured Changelog

This tool generates a `CHANGELOG.md` from git history, using commits since the latest reachable tag. If a repository has no tags, it uses the full commit history.

## Setup

1. Copy `tools/generate-changelog/changelog.sh` into a git repository.
2. Run `bash tools/generate-changelog/changelog.sh . CHANGELOG.md`.
3. Review and commit the generated `CHANGELOG.md`.

## Behavior

- Reads commits since the latest tag with `git log`.
- Skips merge commits.
- Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Links commits automatically when the repository remote is on GitHub.
- Writes a complete Markdown changelog to the requested output path.

## Example

```bash
bash tools/generate-changelog/changelog.sh . tools/generate-changelog/SAMPLE_CHANGELOG.md
```

See `SAMPLE_CHANGELOG.md` for output generated from this repository.
