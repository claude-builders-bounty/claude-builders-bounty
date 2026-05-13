---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a repository's git history.
---

# Generate Changelog

Use this skill when a user asks to create, refresh, or draft a changelog from git history.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run `bash changelog.sh` to generate `CHANGELOG.md` from commits since the latest tag.
3. Review the generated sections and edit wording only when a commit subject is unclear.

## Categories

- `Added`: feature, add, new, introduce, create, implement.
- `Fixed`: fix, bugfix, hotfix, bug, repair, patch, resolve.
- `Changed`: refactor, docs, chore, test, perf, build, and uncategorized commits.
- `Removed`: remove, delete, drop, deprecate.
