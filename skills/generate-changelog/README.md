# Generate Changelog

Generate a structured `CHANGELOG.md` from git history since the most recent tag.

## Setup

1. Copy `changelog.sh` and `skills/generate-changelog/` into a git repository.
2. Run `bash changelog.sh --repo . --output CHANGELOG.md`.
3. Review the generated categories before publishing the release notes.

## Output

The script writes an `Unreleased` changelog with `Added`, `Fixed`, `Changed`, and
`Removed` sections. Conventional commit prefixes are used when present, and
unknown commit subjects are kept under `Changed`.

Relative output paths are resolved inside the target repository, so
`--repo /path/to/project --output CHANGELOG.md` writes to that project's root.
