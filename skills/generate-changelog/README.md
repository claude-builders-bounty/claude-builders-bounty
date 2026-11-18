# `/generate-changelog` Skill & CLI

Generates a categorized `CHANGELOG.md` (`Added`, `Fixed`, `Changed`, `Removed`) from commits since the latest git tag.

## Setup (3 Steps)

1. Copy `SKILL.md` into `.claude/skills/generate-changelog/SKILL.md` (or `~/.claude/skills/generate-changelog/SKILL.md`).
2. Make the script executable: `chmod +x changelog.sh`.
3. Run `/generate-changelog` inside Claude Code or execute `bash changelog.sh CHANGELOG.md v1.4.0`.
