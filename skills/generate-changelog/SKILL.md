# Generate Changelog

Use this skill when a user asks to create or refresh a structured `CHANGELOG.md` from git history.

## Workflow

1. Run `bash changelog.sh` from the target repository root.
2. Review the generated `CHANGELOG.md` categories: `Added`, `Fixed`, `Changed`, and `Removed`.
3. If the user wants a specific heading, rerun with `CHANGELOG_VERSION=<version> bash changelog.sh`.

## Notes

- The script uses commits since the latest git tag.
- If the repository has no tags, it uses the full reachable history.
- Merge commits are ignored so release notes focus on user-facing changes.
