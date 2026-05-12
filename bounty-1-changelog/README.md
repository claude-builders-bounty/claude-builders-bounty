# Generate Changelog Skill

Generate a structured CHANGELOG.md from git history with automatic commit categorization.

## Setup

1. **Copy the skill file** into your Claude Code skills directory:
   ```bash
   cp bounty-1-changelog/SKILL.md .claude/skills/generate-changelog.md
   ```

2. **Run it** -- choose one method:
   - **Claude Code:** type `/generate-changelog` in any git repository
   - **Standalone bash:** run `bash bounty-1-changelog/changelog.sh` from your repo root

3. **Review** the generated `CHANGELOG.md` and commit it when ready.

## How It Works

- Finds the latest git tag and collects all commits since that tag (or all commits if no tags exist)
- Categorizes commits using conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
- Falls back to keyword heuristics when no prefix is found (e.g., "add", "fix", "remove")
- Outputs a [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) formatted file with sections: **Added**, **Fixed**, **Changed**, **Removed**
- Preserves existing changelog entries when appending new versions
