# SKILL: Auto Changelog Generator

## /generate-changelog

Generate a structured CHANGELOG.md from git history.

**Usage:**
```bash
./skills/changelog-generator/changelog.sh /path/to/repo
```

**Features:**
- Auto-categorizes commits into Added / Fixed / Changed / Removed
- Fetches commits since the last git tag
- Outputs standard Keep-a-Changelog format

**Example:**
```bash
# From within a project
./skills/changelog-generator/changelog.sh .
# Creates CHANGELOG.md
```
