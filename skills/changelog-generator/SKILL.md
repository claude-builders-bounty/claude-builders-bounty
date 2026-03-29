---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, auto-categorizing commits into Added, Fixed, Changed, and Removed sections.
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from git commit history since the last git tag.

## Instructions

1. Determine the most recent git tag. If no tags exist, use the initial commit as the starting point.
2. Fetch all commits since that tag using `git log`.
3. Parse each commit message and categorize it based on conventional commit prefixes and keywords:
   - **Added**: commits starting with `feat:`, `feat(`, or containing keywords like "add", "new", "introduce", "implement", "create"
   - **Fixed**: commits starting with `fix:`, `fix(`, or containing keywords like "fix", "bug", "patch", "resolve", "correct"
   - **Changed**: commits starting with `refactor:`, `perf:`, `style:`, `docs:`, `build:`, `ci:`, `chore:`, or containing "update", "change", "improve", "enhance", "modify", "refactor", "migrate"
   - **Removed**: commits starting with `revert:` or containing keywords like "remove", "delete", "deprecate", "drop", "clean up"
   - If a commit doesn't match any category, place it under **Changed** as the default.
4. Generate a `CHANGELOG.md` file in the repository root with the following format:

```markdown
# Changelog

## [Unreleased] — YYYY-MM-DD

### Added
- commit message (short hash)

### Fixed
- commit message (short hash)

### Changed
- commit message (short hash)

### Removed
- commit message (short hash)
```

5. Omit any section that has zero entries (don't print empty headings).
6. Strip conventional commit prefixes from the displayed message (e.g., `feat: add login` becomes `add login`).
7. Include the short commit hash in parentheses after each entry for traceability.
8. If a `CHANGELOG.md` already exists, prepend the new release section below the `# Changelog` header, preserving previous entries.
9. Print a summary of how many commits were categorized and into which sections.

## Example Output

```markdown
# Changelog

## [Unreleased] — 2026-03-28

### Added
- add user authentication flow (a1b2c3d)
- implement dark mode toggle (d4e5f6a)

### Fixed
- fix memory leak in WebSocket handler (b7c8d9e)

### Changed
- update dependency versions (f0a1b2c)
- refactor database connection pooling (c3d4e5f)
```
