---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
trigger: /generate-changelog
---

# Generate Changelog

Generate a structured CHANGELOG.md from your project's git history.

## Usage

```bash
bash changelog.sh
```

Or via Claude Code: `/generate-changelog`

## How it works

1. Finds the last git tag
2. Extracts all commits since that tag
3. Categorizes by conventional commit prefix:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `refactor:`, `chore:`, `perf:` → **Changed**
   - `remove:`, `delete:` → **Removed**
4. Outputs `CHANGELOG.md`

## Configuration

Edit the script to customize categories or add new ones.
