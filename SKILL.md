# CHANGELOG Generator Skill 📝

Automatically generate a structured `CHANGELOG.md` from your project's git history.

## Commands
- `/generate-changelog`: Fetches all commits since the last tag and categorizes them.

## Features
- Auto-categorization: `Added`, `Fixed`, `Changed`, `Removed`.
- Smart detection: Finds the latest git tag automatically.
- Clean formatting: Outputs standard Markdown.

## Usage (for Claude)
When asked to generate a changelog, run the following:
```bash
python3 tools/generate_changelog_v2.py
```
