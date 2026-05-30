# Generate Changelog

Create a structured `CHANGELOG.md` from the current repository's git history.

## Usage

Run this skill when the user asks for `/generate-changelog`, a changelog from git history, or a release-note draft.

## Steps

1. Run `bash changelog.sh` from the repository root.
2. Inspect `CHANGELOG.md` and confirm commits are grouped into `Added`, `Fixed`, `Changed`, and `Removed`.
3. If the user wants a custom destination, rerun with `CHANGELOG_OUTPUT=path/to/file.md bash changelog.sh`.

## Notes

- The script reads commits since the latest git tag.
- If the repository has no tags, it reads the full commit history.
- No external dependencies are required beyond Bash and Git.
