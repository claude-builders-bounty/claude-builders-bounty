# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy or run `scripts/changelog.sh` from the root of any git repository.
2. Run `bash scripts/changelog.sh` to write `CHANGELOG.md`.
3. Review the generated sections and commit the result.

## Files

- `SKILL.md` documents the Claude Code workflow.
- `scripts/changelog.sh` is the standalone generator.
- `tests/test_changelog.sh` checks tag range detection and categories.
- `sample-output.md` shows output from a real GitHub repository.
