# Changelog generator

A tiny `bash changelog.sh` tool that builds a structured `CHANGELOG.md` from the commits since the last git tag.

## Setup
1. Put `changelog.sh` in your repository root.
2. Run `bash changelog.sh`.
3. Open the generated `CHANGELOG.md`.

## Notes
- Commits are grouped into `Added`, `Fixed`, `Changed`, and `Removed`.
- If no git tag exists, the script uses the full commit history.
- You can pass a custom output path: `bash changelog.sh docs/CHANGELOG.md`.

## Test evidence
See `sample-output.md` for a sample run generated from a real GitHub repo clone during testing.
