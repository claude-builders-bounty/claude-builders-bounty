# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `skills/generate-changelog` into a git repository.
2. Run `bash skills/generate-changelog/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Output

The changelog is grouped into `Added`, `Fixed`, `Changed`, and `Removed` sections. If the repository has no tags, the script uses all reachable commits.
