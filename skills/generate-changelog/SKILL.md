---
name: generate-changelog
description: Generate a structured Keep-a-Changelog CHANGELOG.md from git commits since the latest tag.
---

# `/generate-changelog`

Generate or update `CHANGELOG.md` from the current repository's git history.

## Workflow

1. Locate the most recent tag with `git describe --tags --abbrev=0`. If the repository has no tags yet, inspect the full commit log (`HEAD`); otherwise inspect `<latest-tag>..HEAD`.
2. Run `bash skills/generate-changelog/changelog.sh CHANGELOG.md` (or pass a target release label as the second argument, e.g. `bash skills/generate-changelog/changelog.sh CHANGELOG.md v1.4.0`).
3. Verify each commit is grouped under the right Keep-a-Changelog heading while merge commits and automated release commits are excluded:
   - **Added**: `feat`, `feat(scope)`, `add`, `implement`, `create`, `introduce`
   - **Fixed**: `fix`, `fix(scope)`, `bug`, `patch`, `resolve`, `hotfix`
   - **Removed**: `remove`, `delete`, `drop`, `deprecate`, `revert`
   - **Changed**: `refactor`, `perf`, `docs`, `chore`, `ci`, `test`, `style`, and other commits
4. Review the generated `CHANGELOG.md` and print a brief count of entries per section.
