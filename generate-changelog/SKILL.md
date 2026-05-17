---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag.
---

# Generate Changelog

Use this skill when the user asks to generate, refresh, or draft a CHANGELOG from git commits.

## Steps

1. From the target repository root, run:

```bash
bash generate-changelog/changelog.sh
```

2. Review `CHANGELOG.md` and keep the four required sections:

- Added
- Fixed  
- Changed
- Removed

3. If the user provides a release version, run with:

```bash
CHANGELOG_VERSION=v1.2.3 bash generate-changelog/changelog.sh
```

## How it works

Uses `generate_changelog.py` — a dependency-free Python script that reads commits since the latest git tag, classifies commit subjects into changelog sections, and writes a formatted release block.

## Category rules

- Added: feat, add, create, implement, introduce, new
- Fixed: fix, bugfix, bug, repair, resolve, patch
- Changed: change: change, update, refactor, improve, enhance, perf, docs, test, ci, build, chore
- Removed: remove, delete, drop, deprecate
