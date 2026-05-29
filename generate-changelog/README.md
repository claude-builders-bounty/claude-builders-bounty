# Generate Changelog

Create a structured `CHANGELOG.md` from git history.

## Setup

1. Copy `generate-changelog/` into a git repository.
2. Run `bash generate-changelog/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## What It Does

- Finds commits since the latest tag, or all commits if the repo has no tags.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown changelog with commit hashes for traceability.

## Examples

```bash
bash generate-changelog/changelog.sh
bash generate-changelog/changelog.sh --from v1.0.0 --version 1.1.0
bash generate-changelog/changelog.sh --output docs/CHANGELOG.md --dry-run
```

See `examples/sample-output.md` for sample output generated from this repository.
