# Generate Changelog

Generate a structured `CHANGELOG.md` from git history with a Claude Code friendly workflow.

## What it does

- Finds the latest git tag with `git describe --tags --abbrev=0`
- Falls back to the initial commit when the repo has no tags
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`
- Writes a deterministic `CHANGELOG.md` with the current date and commit range

## Usage

1. Copy this skill folder into your Claude skills directory.
2. Run `/generate-changelog` or `bash changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` and commit it.

## Notes

- Conventional prefixes like `feat:` and `fix:` are mapped automatically.
- Commits that do not match a category are placed in `Changed`.
- A sample output lives in `examples/sample-CHANGELOG.md`.
