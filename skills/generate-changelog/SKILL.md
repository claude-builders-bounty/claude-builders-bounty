---
name: generate-changelog
description: Automatically inspects git commit history since the latest release tag and appends a structured Keep-a-Changelog section to CHANGELOG.md.
---

# Git Changelog Generator Skill

This skill analyzes git commits since the last tag and categorizes them automatically into:
- **Added**: New features (feat, add)
- **Fixed**: Bug fixes and patches (fix, bug)
- **Changed**: Refactors, updates, performance tweaks
- **Removed**: Deprecations, deletions

## How to use:
1. Run command:
   ```bash
   python changelog.py [Version]
   ```
2. Or in bash:
   ```bash
   bash changelog.sh [Version]
   ```
