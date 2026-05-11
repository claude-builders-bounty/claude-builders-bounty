# Generate Changelog Skill

Create a categorized `CHANGELOG.md` from git commits since the latest tag.

## Setup in 3 steps

1. Copy `skills/generate-changelog` into your Claude Code skills folder or keep it in any repo.
2. From the project you want to summarize, run `bash /path/to/skills/generate-changelog/scripts/changelog.sh`.
3. Review the generated `CHANGELOG.md` and commit it with your release changes.

## Examples

```bash
bash skills/generate-changelog/scripts/changelog.sh
bash skills/generate-changelog/scripts/changelog.sh --from v1.0.0 --to HEAD
bash skills/generate-changelog/scripts/changelog.sh --repo ../my-project --output /tmp/CHANGELOG.md
```

The generated changelog includes `Added`, `Fixed`, `Changed`, `Removed`, and optional `Breaking Changes` sections.
