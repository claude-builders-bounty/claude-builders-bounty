# Generate Changelog Skill

Create a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy `scripts/changelog.sh` into the target git repository.
2. Run `bash scripts/changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` before committing it.

## Slash Command

Use `/generate-changelog` to run this skill in Claude Code, or run the script
directly with Bash:

```bash
bash scripts/changelog.sh
```

The output is grouped into `Added`, `Fixed`, `Changed`, and `Removed`.
