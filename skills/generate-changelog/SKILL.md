---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history since the latest git tag, categorized into Added, Fixed, Changed, and Removed.
---

# `/generate-changelog` Skill

When invoked via `/generate-changelog`, follow these steps:

1. **Locate Latest Git Tag**:
   - Run `git describe --tags --abbrev=0 2>/dev/null` to determine the most recent tag. If no tag exists, inspect all commits up to `HEAD`.
2. **Collect & Categorize Commits**:
   - Run `bash changelog.sh` (or `git log <last-tag>..HEAD --no-merges --pretty=format:"%h|%s|%cs"`) and classify each commit into:
     - **Added**: `feat`, `add`, `new`, `create`, `implement`
     - **Fixed**: `fix`, `bug`, `hotfix`, `patch`, `resolve`
     - **Removed**: `remove`, `delete`, `drop`, `deprecate`, `clean`
     - **Changed**: `refactor`, `perf`, `chore`, `docs`, `update`, and all other commits
3. **Write `CHANGELOG.md`**:
   - Output Keep-a-Changelog compliant Markdown to `CHANGELOG.md` and print a summary of commit counts per section.
