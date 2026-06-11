---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history since the last git tag, categorized into Added, Fixed, Changed, and Removed.
---

# Generate Changelog Skill

Automatically builds a structured `CHANGELOG.md` from git history since the latest tag (or full history if no tags exist).

## Usage

### Via Claude Code Slash Command
```
/generate-changelog
```

### Via CLI Script
```bash
bash changelog.sh [--output CHANGELOG.md] [--repo .] [--version Unreleased]
```

## Categories
- **Added**: `feat`, `add`, `new`, `feature`
- **Fixed**: `fix`, `bugfix`, `hotfix`, `patch`
- **Changed**: `change`, `update`, `refactor`, `perf`, `docs`, `chore`, `style`, `test`, `build`, `ci`
- **Removed**: `remove`, `delete`, `drop`, `deprecate`
