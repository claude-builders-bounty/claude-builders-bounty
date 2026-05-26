# Generate Changelog Skill

Creates a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy or keep `skills/generate-changelog/changelog.sh` in your repository.
2. Run `bash skills/generate-changelog/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Output Sections

- Added
- Fixed
- Changed
- Removed

The script uses conventional commit prefixes and common keywords to place commits into the right section. If no tag exists, it uses the full git history.
