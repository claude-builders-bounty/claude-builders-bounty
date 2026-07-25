---
name: generate-changelog
description: Use when the user wants to generate a structured CHANGELOG.md from git history. Trigger: "/generate-changelog" or "generate changelog" or "create changelog".
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from git history, auto-categorizing commits.

## Usage

Run the script:
```bash
python3 scripts/changelog.py [--since TAG] [--output CHANGELOG.md]
```

Or trigger via Claude Code skill command: `/generate-changelog`

## Behavior

1. Fetches all commits since the latest git tag (or specified tag)
2. Categorizes commits based on Conventional Commits prefixes:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `refactor:`, `perf:`, `style:` → **Changed**
   - `revert:`, `remove:` → **Removed**
   - `security:`, `sec:` → **Security**
   - `docs:`, `chore:`, `ci:`, `test:` → skipped (non-user-facing)
3. Uncategorized commits go under **Changed**
4. Outputs valid Keep a Changelog format

## Setup (2 commands)

```bash
chmod +x scripts/changelog.py
python3 scripts/changelog.py --since $(git describe --tags --abbrev=0 2>/dev/null || echo "")
```
