# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `scripts/changelog.sh` and this `skills/generate-changelog` directory into a git repository.
2. Run `bash scripts/changelog.sh --dry-run` to preview the generated changelog.
3. Run `bash scripts/changelog.sh --output CHANGELOG.md` to write the file.

## Options

- `--since <tag-or-ref>`: choose a custom starting tag or commit.
- `--output <file>`: write to a custom changelog path.
- `--dry-run`: print the generated changelog without writing a file.

