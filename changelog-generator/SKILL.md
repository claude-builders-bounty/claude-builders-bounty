# CHANGELOG Generator Skill

Generate structured CHANGELOG.md files from git history.

## Usage

From Claude Code, use the slash command:


Or from terminal:


## What it does

1. Finds the latest git tag
2. Fetches all commits since that tag
3. Categorizes commits into: Added, Fixed, Changed, Removed
4. Recognizes conventional commit prefixes (feat:, fix:, etc.)
5. Outputs formatted CHANGELOG.md

## Requirements

- Python 3.6+
- Git
- Bash (for wrapper script)
