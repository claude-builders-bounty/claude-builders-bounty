# CHANGELOG Generator for Claude Code

Auto-generate structured CHANGELOG.md from git history.

## Setup (3 steps)

1. Install the skill: copy `SKILL.md` to your project's `.claude/skills/` directory
2. Add the script: copy `scripts/changelog.py` anywhere in your project
3. Run: `/generate-changelog` in Claude Code, or `python scripts/changelog.py --since v1.0.0`

## Features

- Fetches commits since last git tag (or specified tag)
- Auto-categorizes into: Added / Fixed / Changed / Removed / Security
- Follows [Keep a Changelog](https://keepachangelog.com/) format
- Appends to existing CHANGELOG without overwriting

## Usage

```bash
# Generate since last tag
python scripts/changelog.py

# Generate since specific tag
python scripts/changelog.py --since v2.0.0

# Write to file
python scripts/changelog.py --since v1.0.0 --output CHANGELOG.md
```

## Sample

See [sample-output.md](sample-output.md) — generated from a real 500+ star open-source security tool with 90+ categorized commits.
