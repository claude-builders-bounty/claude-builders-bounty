# Generate Changelog Skill

This skill enables Claude Code to automatically generate and update `CHANGELOG.md` from git history.

## Usage
Run `/generate-changelog` in Claude Code, or execute `./scripts/changelog.sh` in your terminal.

## Instructions
When invoked:
1. Execute `scripts/changelog.sh` to analyze git commits since the last tag.
2. Present the generated changelog preview to the user.
3. Confirm that `CHANGELOG.md` has been successfully updated.
