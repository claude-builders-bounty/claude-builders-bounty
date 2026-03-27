---
name: generate-changelog
description: Auto-generate structured CHANGELOG.md from git history since last tag.
---

# generate-changelog

Generate a structured `CHANGELOG.md` from git commit history.

## Usage

```bash
python3 changelog-tool/generate_changelog.py
```

## How It Works

1. Finds the most recent git tag
2. Fetches all commits since that tag
3. Auto-categorizes each commit by keyword:
   - **Added**: feat, add, new, implement, create
   - **Fixed**: fix, bug, patch, resolve
   - **Changed**: update, improve, refactor, rename
   - **Removed**: remove, delete, drop, deprecate
4. Generates a formatted CHANGELOG.md (prepends to existing)
