# generate-changelog

Three steps:

1. Copy `scripts/changelog.sh` into your repo (or run from this folder).
2. From the repository root: `bash scripts/changelog.sh`
3. Review `CHANGELOG.md` (commits since the latest git tag, grouped by conventional-commit type).

Optional: `bash scripts/changelog.sh -o docs/RELEASE-NOTES.md`

Cursor / Claude Code: install `skills/generate-changelog/SKILL.md` and run `/generate-changelog`.
