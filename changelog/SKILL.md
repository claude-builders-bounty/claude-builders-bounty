---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# Generate Changelog

Generates a structured CHANGELOG.md from git history, auto-categorizing commits.

## Usage

```bash
bash generate-changelog.sh [--since-tag TAG] [--output FILE]
```

Or use `/generate-changelog` in Claude Code.

## Categories
- **Added**: feat commits
- **Fixed**: fix commits
- **Changed**: refactor/update commits
- **Removed**: remove/delete/deprecated commits

## Examples

```bash
# Generate changelog from last tag
bash generate-changelog.sh

# Generate since specific tag
bash generate-changelog.sh --since-tag v1.0.0

# Custom output file
bash generate-changelog.sh --output HISTORY.md
```
