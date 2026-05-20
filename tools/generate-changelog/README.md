# Generate Changelog

Generate a structured `CHANGELOG.md` from the commits since the latest git tag.
If the repository has no tags, the script includes the full git history.

## Setup

1. Copy `tools/generate-changelog/changelog.sh` into any git repository.
2. Run `bash tools/generate-changelog/changelog.sh`.
3. Review the generated `CHANGELOG.md` and commit it.

## Claude Code command

Copy `.claude/commands/generate-changelog.md` into your project to enable:

```text
/generate-changelog
```

## Output categories

- `Added`: `feat`, `add`, `create`, `initial`
- `Fixed`: `fix`, `bug`, `patch`, `repair`
- `Changed`: `docs`, `refactor`, `test`, `chore`, or uncategorized commits
- `Removed`: `remove`, `delete`, `drop`, `deprecate`
