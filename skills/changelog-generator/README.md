# CHANGELOG Generator — Claude Code Skill

A Claude Code skill that generates structured CHANGELOG.md from git history.

## Setup

1. **Copy files** to your project:
   ```bash
   cp skills/changelog-generator/skill.md .claude/skills/
   cp skills/changelog-generator/changelog.sh .claude/scripts/
   chmod +x .claude/scripts/changelog.sh
   ```

2. **Reload skills** in Claude Code:
   ```
   /skill reload
   ```

## Usage

```
/generate-changelog
```

Or directly:
```bash
bash .claude/scripts/changelog.sh
bash .claude/scripts/changelog.sh --repo /path/to/repo --output CHANGELOG.md
```

## Features

- Parses conventional commits (feat:, fix:, BREAKING CHANGE:, chore:, etc.)
- Keyword fallback for non-conventional messages
- Auto-categorizes into: Added / Fixed / Changed / Removed / Internal
- Handles edge cases: no tags, no commits, empty repos
- Configurable repo path and output file

## Requirements

- Git 2.x
- Bash 4+
- A git repository with at least one tag
