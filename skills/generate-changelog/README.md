# 📝 Structured Git `CHANGELOG.md` Generator (`/generate-changelog`)

Zero-dependency Claude Code skill (`SKILL.md`) and CLI tool (`bash changelog.sh` / `generate_changelog.py`) that generates a Keep-a-Changelog compliant `CHANGELOG.md` from git history since the last tag, automatically categorized into **`Added`**, **`Fixed`**, **`Changed`**, and **`Removed`**.

## Quick Setup (3 Steps)

1. **Copy the skill & script into your project (or `~/.claude/skills/generate-changelog/`):**
   ```bash
   chmod +x changelog.sh generate_changelog.py
   ```
2. **Generate `CHANGELOG.md` since the latest git tag:**
   ```bash
   bash changelog.sh
   ```
3. **(Optional) Specify a custom tag range or release version:**
   ```bash
   bash changelog.sh --since v1.0.0 --version 1.1.0 --output CHANGELOG.md
   ```
   Or invoke directly inside Claude Code via `/generate-changelog`.
