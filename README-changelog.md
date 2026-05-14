# Generate a changelog from git history

This adds a small `changelog.sh` command for bounty #1. It reads commits since the latest git tag, groups them into Added, Fixed, Changed, and Removed, then writes a Markdown `CHANGELOG.md`.

## Setup

1. Copy `changelog.sh` into a git repository.
2. Run `chmod +x changelog.sh`.
3. Run `bash changelog.sh` or `bash changelog.sh SAMPLE_CHANGELOG.md`.

## Notes

- If the repo has tags, the script uses commits after the latest tag.
- If there are no tags, it uses the full commit history.
- Conventional commit prefixes such as `feat:`, `fix:`, `refactor:`, and `remove:` are categorized automatically.

