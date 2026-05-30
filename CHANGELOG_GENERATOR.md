# Changelog Generator

Generate a structured `CHANGELOG.md` from git commits since the last tag.

## Setup

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md` and commit it.

## Categories

The script groups commits into:

- `Added`: `feat:`, `feat!:`, `add:`, `added:`
- `Fixed`: `fix:`, `bug:`, `bugfix:`
- `Removed`: `remove:`, `removed:`, `delete:`, `deleted:`
- `Changed`: everything else, including docs, chores, tests, and refactors

If a repository has tags, only commits since the latest tag are included. If it has no tags, the script uses the full project history.
