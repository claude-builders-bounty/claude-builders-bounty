# Generate Changelog

Use this skill when the user asks to generate or update a structured `CHANGELOG.md` from git history.

## Instructions

1. Confirm the current directory is a git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` and report the output path.

## Behavior

The script:

- Uses commits since the latest git tag when a tag exists.
- Falls back to all commits when no tags exist.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a formatted `CHANGELOG.md`.
