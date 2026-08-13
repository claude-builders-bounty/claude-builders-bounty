---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history."
tags: [git, changelog, automation]
---

# Generate Changelog

Generate a structured CHANGELOG.md from a project's git history.

## Usage

### As a Bash Script
```bash
bash changelog.sh [output_file]
```

### As a Claude Code Command
```
/generate-changelog
```

## How it Works

1. Fetches commits since the last git tag (or all commits if no tags)
2. Auto-categorizes into: Added / Fixed / Changed / Removed
3. Outputs a properly formatted CHANGELOG.md

## Categories

Commits are categorized by their prefix:
- `feat:` / `add:` / `new:` → **Added**
- `fix:` / `bugfix:` / `patch:` → **Fixed**
- `refactor:` / `change:` / `update:` / `improve:` → **Changed**
- `remove:` / `delete:` → **Removed**
- Other → **Other**

## Requirements

- Git repository with commits
- Bash shell
