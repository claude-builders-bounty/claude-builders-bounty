---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag
command: /generate-changelog
---

# Generate Changelog

Generate a structured `CHANGELOG.md` by analyzing git commits since the last tag.

## Instructions

When the user runs `/generate-changelog`, do the following:

1. Find the most recent git tag with `git describe --tags --abbrev=0`. If no tags exist, use the full history.
2. Get all non-merge commits since that tag with `git log <tag>..HEAD --pretty=format:'%H|%s|%an' --no-merges`.
3. Categorize each commit by its prefix:
   - **Added**: commits starting with `feat`, `add`, `new`, `create`, `implement`, `introduce`, `support`
   - **Fixed**: commits starting with `fix`, `bug`, `patch`, `resolve`, `correct`, `repair`, `hotfix`
   - **Removed**: commits starting with `remove`, `delete`, `drop`, `deprecate`, `strip`, `clean`
   - **Changed**: everything else
4. Write a `CHANGELOG.md` with this structure:

```markdown
# Changelog

## [repo-name] — Changes since <tag> (YYYY-MM-DD)

### Added
- commit message (`abc1234` by Author Name)

### Fixed
- ...

### Changed
- ...

### Removed
- ...
```

5. Only include categories that have entries.
6. Report the total number of entries and which categories were found.

Alternatively, the user can run `bash skills/generate-changelog/changelog.sh` directly from the terminal.
