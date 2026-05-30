# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from git history.

## Setup

1. Copy `skills/generate-changelog/` and `changelog.sh` into a git repository.
2. Run `bash changelog.sh` to generate `CHANGELOG.md` from commits since the latest git tag.
3. Optionally pass `--range <rev>` or `--version <name>` for a custom release.
