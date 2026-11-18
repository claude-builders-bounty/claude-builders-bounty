---
name: generate-changelog
description: Generate a structured CHANGELOG.md (Added, Fixed, Changed, Removed) from git commit history since the latest tag.
---

# `/generate-changelog`

Analyze the repository's git history since the last semantic version tag (or initial commit if no tag exists) and write a structured Keep-a-Changelog style `CHANGELOG.md`.

## Steps
1. Determine the previous git tag via `git describe --tags --abbrev=0 2>/dev/null` (fallback to the root commit).
2. Run `bash changelog.sh` (or parse `git log <range> --pretty=format:"%h|%s"`).
3. Classify each commit into one of four sections:
   - **Added**: commits starting with `feat`, `add`, `new`, `implement`
   - **Fixed**: commits starting with `fix`, `bug`, `hotfix`, `patch`, `resolve`
   - **Removed**: commits starting with `remove`, `delete`, `drop`, `deprecate`, or `feat!:` breaking removals
   - **Changed**: `refactor`, `perf`, `chore`, `docs`, `ci`, `build`, `update`, or other modifications
4. Prepend or write the new version section to `CHANGELOG.md` and show a summary of categorized commits.
