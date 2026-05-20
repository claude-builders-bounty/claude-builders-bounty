# Generate Changelog

Create a structured `CHANGELOG.md` from git history with `Added`, `Fixed`, `Changed`, and `Removed` sections.

## Setup

1. Copy `changelog.sh` and the `generate-changelog/` folder into the root of a git repository.
2. Run `bash changelog.sh --stdout` to preview the changelog.
3. Run `bash changelog.sh` to write `CHANGELOG.md`.

## Notes

- By default, commits are read from the latest git tag to `HEAD`.
- If the repository has no tags, the script includes all commits.
- Use `bash changelog.sh --from <ref>` to override the lower bound.
- Use `bash changelog.sh --output <file>` to write to a different path.
- Use `bash generate-changelog/scripts/test-changelog.sh` to run a smoke test in a temporary git repository.
