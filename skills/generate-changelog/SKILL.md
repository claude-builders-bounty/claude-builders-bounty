---
name: generate-changelog
description: Automatically generates or updates a structured CHANGELOG.md from git commit history since the last release tag.
---

# Git Changelog Generator Skill

Automatically generates or updates your project's `CHANGELOG.md` file by inspecting git history since the most recent git tag.

## How to use

Run the changelog script directly:

```bash
bash skills/generate-changelog/changelog.sh [version_name] [output_file]
```

### Examples:
- Generate unreleased changelog: `bash skills/generate-changelog/changelog.sh`
- Generate for version v1.2.0: `bash skills/generate-changelog/changelog.sh v1.2.0`

## Categorization Rules
- **Added**: Commits starting with `feat:`, `add:`, `new:`, `implement:`
- **Fixed**: Commits starting with `fix:`, `bug:`, `patch:`, `hotfix:`
- **Changed**: Commits starting with `refactor:`, `perf:`, `chore:`, `docs:`, `style:`
- **Removed**: Commits starting with `remove:`, `delete:`, `deprecate:`, `revert:`
