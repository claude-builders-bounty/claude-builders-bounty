---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# Generate Changelog

Auto-generates a structured `CHANGELOG.md` from git commits since the last tag.

## Usage

```
/generate-changelog [repo-path]
```

Or via bash:

```bash
bash bounties/bounty-001-changelog/changelog.sh [repo-path]
```

## What It Does

1. Finds the last git tag (or starts from initial commit)
2. Scans all commits since that tag
3. Categorizes each commit:
   - **Added** — feat, add, create, implement
   - **Fixed** — fix, patch, bug, resolve
   - **Removed** — remove, delete, deprecate
   - **Changed** — everything else
4. Writes a beautiful `CHANGELOG.md` with emoji headers
