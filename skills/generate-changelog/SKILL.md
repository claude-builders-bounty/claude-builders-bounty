---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history since the last tag. Auto-categorizes commits into Added/Fixed/Changed/Removed using conventional commit prefixes.
---

# Generate Changelog

## Quick Start

```bash
# 1. Make executable
chmod +x changelog.sh

# 2. Run in any git repo
./changelog.sh

# 3. Output: CHANGELOG.md
```

## Requirements
- git
- bash 4+

## How it works

1. Finds the latest git tag (`git describe --tags --abbrev=0`)
2. Collects all commits since that tag
3. Categorizes each commit based on conventional commit prefixes:
   - `feat:` / `add:` → **Added**
   - `fix:` / `bug:` → **Fixed**
   - `refactor:` / `perf:` / `style:` / `chore:` / `deps:` → **Changed**
   - `remove:` / `drop:` / `revert:` → **Removed**
   - Uncategorized → **Changed**
4. Outputs a clean `CHANGELOG.md` with version, date, and categorized entries
