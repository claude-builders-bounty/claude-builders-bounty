# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag. If the repository has no tags, the script uses the full history.

## Setup

1. Copy `tools/generate-changelog/` into any git repository.
2. Run `python tools/generate-changelog/generate_changelog.py` or `bash tools/generate-changelog/changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` and commit it.

## Categorization

Commits are grouped by their subject prefix:

- `feat:` or `add:` -> `Added`
- `fix:`, `bug:`, or `hotfix:` -> `Fixed`
- `remove:`, `delete:`, `drop:`, or `deprecate:` -> `Removed`
- `change:`, `update:`, `refactor:`, `perf:`, `docs:`, `test:`, `chore:`, `build:`, or `ci:` -> `Changed`

Subjects without a known prefix are placed under `Changed` so they are still visible in the changelog.
