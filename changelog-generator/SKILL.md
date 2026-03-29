---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from a project's git history.

## Steps

1. **Determine the range**
   - If a `CHANGELOG.md` exists, find the last version header and use the tag after it as start
   - Otherwise, find the most recent git tag and use it as start
   - If no tags exist, start from the first commit

2. **Collect commits**
   - Run `git log --pretty=format:"%s" <range>` to get commit subjects
   - Parse each commit message for conventional commit prefixes

3. **Categorize**
   - `feat:`, `feature:` → **Added**
   - `fix:` → **Fixed**
   - `refactor:`, `style:`, `chore:` → **Changed**
   - `remove:`, `deprecate:` → **Removed**
   - Commits without a prefix: use keyword heuristic (`add`, `new` → Added; `fix`, `resolve` → Fixed; etc.)

4. **Generate CHANGELOG.md**
   - Write header: `## [version] - YYYY-MM-DD`
   - Write each non-empty category as `### Category` followed by bullet list
   - Prepend above the existing changelog content (don't overwrite old entries)

5. **Confirm**
   - Print the generated section to the user
   - Ask if they want to commit it

## Version Detection

- If the last tag is `v1.2.3`, next version is `v1.2.4`
- If no tags, use `0.1.0`

## Example Output

```markdown
# Changelog

## [0.2.0] - 2026-03-29

### Added
- feat: add user authentication endpoint
- feat: implement dark mode toggle
- new dashboard analytics page

### Fixed
- fix: resolve login redirect loop
- patch memory leak in data processor

### Changed
- refactor: simplify database query builder

### Removed
- remove deprecated v1 API endpoints
```
