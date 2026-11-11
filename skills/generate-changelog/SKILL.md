---
name: generate-changelog
description: Automatically generates a structured, Keep-a-Changelog compliant CHANGELOG.md from git commit history since the last release tag.
triggers:
  - "/generate-changelog"
  - "generate changelog"
  - "update changelog"
---

# Generate Changelog Skill

Generate a structured, human-readable `CHANGELOG.md` file from the repository's git commit history.

## What it does
1. Identifies the latest git release tag (`git describe --tags --abbrev=0`).
2. Extracts all commits between the tag and `HEAD` (or all commits if no tags exist).
3. Automatically parses and categorizes commits into:
   - **Added**: New features, capabilities, endpoints (`feat:`, `add:`, `new:`)
   - **Fixed**: Bug fixes, patch repairs, hotfixes (`fix:`, `patch:`, `resolve:`)
   - **Changed**: Refactors, performance updates, docs, chores (`refactor:`, `perf:`, `docs:`, `chore:`)
   - **Removed**: Deprecations and removed features (`remove:`, `deprecate:`, `delete:`)
4. Formats entries in accordance with [Keep a Changelog](https://keepachangelog.com/) standards.
5. Safely creates or prepends to the project's `CHANGELOG.md`.

## Execution
Run directly via bash:
```bash
bash skills/generate-changelog/changelog.sh
```

Or preview the output without modifying files:
```bash
bash skills/generate-changelog/changelog.sh --dry-run
```

Specify a release version header:
```bash
bash skills/generate-changelog/changelog.sh --tag v1.2.0
```
