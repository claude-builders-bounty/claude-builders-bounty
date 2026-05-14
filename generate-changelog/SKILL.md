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

## Behavior

- Fetches commits since the latest git tag with `git describe --tags --abbrev=0`.
- If the repo has no tags, uses the full commit history.
- Skips merge commits.
- Categorizes Conventional Commit prefixes and common words into Added, Fixed, Changed, and Removed.
- Writes a properly formatted `CHANGELOG.md`.

## Category rules

- Added: `feat:`, `feature:`, `add:`, `implement`, `introduce`
- Fixed: `fix:`, `bugfix:`, `hotfix:`, `repair`, `resolve`
- Removed: `remove:`, `delete:`
- Changed: `change:`, `update:`, `refactor:`, `perf:`, `docs:`, `test:`, `chore:`, `ci:`, `style:`, `build:`, and uncategorized commits
