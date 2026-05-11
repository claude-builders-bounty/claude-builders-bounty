# Generate Changelog

Use this skill when the user asks to generate, update, or draft a `CHANGELOG.md` from a git repository's commit history.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run `bash changelog.sh --dry-run` to preview the generated changelog.
3. If the preview is correct, run `bash changelog.sh` to write `CHANGELOG.md`.

## Behavior

- Uses commits since the latest reachable git tag.
- Falls back to all commits when no tags exist.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Preserves the previous changelog content under the new generated section when `CHANGELOG.md` already exists.
- Includes short commit SHAs so each entry can be traced back to source history.

## Notes

If the repository uses non-standard commit messages, review the generated grouping and adjust section placement manually before publishing release notes.
