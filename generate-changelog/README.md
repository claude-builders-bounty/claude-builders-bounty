# Git Changelog Generator

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy `changelog.sh` and `generate-changelog/` into any git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Categories

The script maps commit subjects into:

- `Added`: `feat:`, `feature:`, `add:`, `new:`
- `Fixed`: `fix:`, `bug:`, `bugfix:`, `repair:`, `hotfix:`
- `Changed`: `change:`, `refactor:`, `perf:`, `docs:`, `test:`, `build:`, `ci:`, `chore:`, and uncategorized commits
- `Removed`: `remove:`, `delete:`, `drop:`

## Output

By default the command writes `CHANGELOG.md` in the repository root. Pass a file path to write somewhere else:

```bash
bash changelog.sh /tmp/CHANGELOG.md
```

## Test

```bash
bash generate-changelog/test.sh
```
