---
name: generate-changelog
description: Automatically generates a Keep-a-Changelog compliant CHANGELOG.md from git commits since the latest git tag, categorizing commits into Added, Fixed, Changed, and Removed.
command: /generate-changelog
---

# `/generate-changelog` — Claude Code Skill

## Usage
Run `/generate-changelog` inside Claude Code or execute directly via Bash:
```bash
bash changelog.sh CHANGELOG.md .
```

## How It Works
1. Detects the latest Git tag (`git describe --tags --abbrev=0`) or falls back to `HEAD`.
2. Parses `git log` commits and classifies each commit into:
   - **Added** (`feat`, `add`, `new`, `create`, `implement`)
   - **Fixed** (`fix`, `bug`, `hotfix`, `patch`, `resolve`)
   - **Removed** (`remove`, `delete`, `drop`, `clean`, `deprecate`)
   - **Changed** (`refactor`, `update`, `upgrade`, `perf`, and all other improvements)
3. Writes a clean, Keep-a-Changelog structured `CHANGELOG.md`.
