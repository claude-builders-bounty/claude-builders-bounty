# Generate Changelog

Create a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `changelog.sh` into a git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md`.

## Output

Commits are grouped into:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

The script recognizes conventional commit prefixes such as `feat:`, `fix:`, `refactor:`, and `remove:`, then falls back to keyword matching for non-conventional commit messages.
