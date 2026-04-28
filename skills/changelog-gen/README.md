# Structured CHANGELOG Generator Skill 📝

A Claude Code skill that generates a structured CHANGELOG from git history, categorized by commit type.

## Features
- Automatically categorizes commits into Features, Bug Fixes, Documentation, and Refactors.
- Supports generating history since a specific tag or commit hash.
- Clean Markdown output following Keep a Changelog format.

## Usage

```bash
# Generate from all history
python3 skills/changelog-gen/generate-changelog.py

# Generate since a specific tag
python3 skills/changelog-gen/generate-changelog.py v1.0.0
```

## How to use as a Skill
You can ask Claude:
"Generate a structured changelog for this repo since the last tag."
And provide this script as the tool to use.
