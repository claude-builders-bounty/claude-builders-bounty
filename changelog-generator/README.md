# Changelog Generator

Generate a structured `CHANGELOG.md` from git history with auto-categorization.

## Setup (3 steps)

1. Copy `changelog-generator/` into your project
2. Run: `bash changelog.sh` (or `python3 generate_changelog.py`)
3. Check the generated `CHANGELOG.md`

## Features

- Zero external dependencies (bash or Python stdlib only)
- Auto-categorizes commits using conventional commit prefixes
- Falls back to keyword detection for non-conventional messages
- Supports scoped commits: `feat(auth): add login`
- Detects last git tag automatically

## Categories

| Prefix | Category |
|--------|----------|
| `feat:`, `add:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `refactor:`, `update:`, `perf:`, `style:` | Changed |
| `remove:`, `delete:`, `deprecate:` | Removed |

Non-prefixed commits are categorized by leading verb (e.g., "Add feature X" → Added).

## Example Output

```markdown
# Changelog

## [Unreleased] — 2026-05-16

### Added
  - user authentication with OAuth2
  - dark mode toggle

### Fixed
  - memory leak in cache layer
  - typo in README

### Changed
  - simplify API response format
  - upgrade dependencies to latest

### Removed
  - legacy v1 API endpoints
```

## Claude Code Skill

Use as a Claude Code skill by referencing `SKILL.md`:
```
/generate-changelog
```
