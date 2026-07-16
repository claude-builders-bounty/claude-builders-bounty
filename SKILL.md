---
name: changelog
description: Generate a structured CHANGELOG.md from git history. Use when generating changelogs from git commits, creating release notes, or summarizing project changes.
---

# CHANGELOG Generator Skill

Automatically generates a structured `CHANGELOG.md` from git commit history.

## Quick Usage

```bash
# Generate changelog from last tag
bash changelog.sh

# Generate changelog for specific range
bash changelog.sh v1.0.0..v2.0.0

# Output to specific file
bash changelog.sh -o custom_changelog.md
```

## Categories

Commits are auto-categorized by conventional commit prefixes:
- **Added**: feat:, feature:, new:
- **Fixed**: fix:, bugfix:, patch:
- **Changed**: refactor:, change:, modify:
- **Removed**: remove:, delete:, drop:
- **Security**: security:, CVE-, vulnerability:
- **Other**: Everything else

## Requirements

- Git must be installed
- Repository must have at least one tag (creates from first tag if none exists)
- Works with conventional commit messages
