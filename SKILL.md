---
name: generate-changelog
description: >
  Generate a structured CHANGELOG.md from the current repository's git history.
  Categorizes commits into Added, Fixed, Changed, and Removed sections using
  conventional commit prefixes. Detects the latest git tag automatically.
---

# /generate-changelog

Generate a structured `CHANGELOG.md` from this project's git commit history.

## What it does

1. Finds the latest git tag (or uses the full history if no tags exist).
2. Reads all non-merge commits since that tag.
3. Categorizes each commit by its conventional prefix:
   - `feat:`, `add:`, `new:` → **Added**
   - `fix:`, `bug:`, `patch:` → **Fixed**
   - `refactor:`, `perf:`, `style:`, `chore:`, `update:` → **Changed**
   - `remove:`, `delete:`, `revert:` → **Removed**
4. Writes a clean, markdown-formatted `CHANGELOG.md` to the project root.

## How to run

```bash
bash changelog.sh            # default: writes CHANGELOG.md
bash changelog.sh output.md  # custom output filename
```

## Requirements

- Git repository with at least one commit
- Bash (any version) and standard POSIX utilities
- No external dependencies
