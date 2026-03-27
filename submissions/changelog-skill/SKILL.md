---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag
---

# /generate-changelog

Generate a structured CHANGELOG.md from this project's git history.

## Steps

1. Find the latest git tag: `git describe --tags --abbrev=0 2>/dev/null || echo ""`
2. Get commits since that tag (or all commits if no tag): `git log --oneline --pretty=format:"%s" <tag>..HEAD`
3. Categorize each commit by its prefix or content:
   - **Added**: commits containing "feat:", "add", "new", "create", "implement"
   - **Fixed**: commits containing "fix:", "bug", "patch", "resolve", "repair"
   - **Changed**: commits containing "refactor:", "update", "improve", "change", "modify", "enhance"
   - **Removed**: commits containing "remove:", "delete", "drop", "deprecate"
   - **Other**: anything that doesn't match the above
4. Format as a Markdown CHANGELOG with:
   - Version header (use tag name or "Unreleased")
   - Date
   - Categories as H3 headers
   - Each commit as a bullet point
5. Write to CHANGELOG.md in the project root
6. Show a summary of what was generated

## Output Format

```markdown
# Changelog

## [v1.2.0] - 2026-03-27

### Added
- feat: implement user authentication
- add dark mode support

### Fixed
- fix: resolve login timeout issue
- fix: correct pagination offset

### Changed
- refactor: simplify database queries
- update: upgrade dependencies

### Removed
- remove: deprecated API endpoints
```
