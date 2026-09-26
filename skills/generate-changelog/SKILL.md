---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits automatically categorized into Added, Fixed, Changed, and Removed.
---

# Generate Changelog Skill

This skill parses git commit history since the last git tag (or HEAD if no tags exist) and formats it into a clean, categorized `CHANGELOG.md`.

## Features
- **Auto-Categorization**: Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed` based on conventional commit prefixes (`feat:`, `fix:`, `add`, `remove`, etc.).
- **Tag Detection**: Automatically identifies the most recent git tag or accepts a custom starting tag.
- **Hermetic Executable**: Single self-contained Python script with zero third-party dependencies.

## Usage

### 1. Run Python Script
```bash
python3 skills/generate-changelog/generate_changelog.py
```

### 2. Custom Output File or Starting Tag
```bash
python3 skills/generate-changelog/generate_changelog.py -o MY_CHANGELOG.md -t v1.0.0
```
