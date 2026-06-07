---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history since the last tag. Auto-categorizes commits into Added, Fixed, Changed, and Removed sections based on Conventional Commits prefixes.
---

# Changelog Generator

Generate a structured `CHANGELOG.md` from git history.

## Usage

Run `/generate-changelog` or execute the script directly:

```bash
bash changelog-generator/changelog.sh [--output CHANGELOG.md] [--since <tag>]
```

## How It Works

1. Finds the most recent git tag (`git describe --tags --abbrev=0`)
2. Collects all commits since that tag
3. Categorizes commits using Conventional Commits prefixes:
   - `feat:` / `add:` -> **Added**
   - `fix:` / `bug:` -> **Fixed**
   - `refactor:` / `perf:` / `style:` / `deps:` -> **Changed**
   - `revert:` / `remove:` / `drop:` -> **Removed**
4. Writes a formatted `CHANGELOG.md` with the version header
