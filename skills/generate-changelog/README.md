# Structured CHANGELOG Generator (`SKILL.md` + `changelog.sh`)

Automatically generates a structured [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) `CHANGELOG.md` from a repository's git history since the last git tag, categorizing commits into **`Added`**, **`Fixed`**, **`Changed`**, and **`Removed`**.

## Setup in 3 Steps

1. **Copy the skill into your project or Claude Code skills directory**:
   ```bash
   mkdir -p ~/.claude/skills/generate-changelog
   cp SKILL.md changelog.py changelog.sh ~/.claude/skills/generate-changelog/
   ```
2. **Run via CLI or Claude Code slash command**:
   ```bash
   bash changelog.sh --repo . --output CHANGELOG.md
   # or inside Claude Code: /generate-changelog
   ```
3. **Verify tests**:
   ```bash
   pytest test_changelog.py
   ```
