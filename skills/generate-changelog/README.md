# Generate Changelog Skill

This skill allows Claude Code or any developer to automatically generate a structured `CHANGELOG.md` file based on the git history. It fetches commits since the last git tag, categorizes them appropriately (Added, Fixed, Changed, Removed), and formats them cleanly into Markdown.

## Setup

1. Copy the `generate-changelog` folder into your project's `.claude/skills/` directory.
2. Make the script executable: `chmod +x .claude/skills/generate-changelog/changelog.sh`
3. The skill will now be available to your Claude Code agent! You can also run it manually via `bash .claude/skills/generate-changelog/changelog.sh`.
