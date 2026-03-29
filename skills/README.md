# Generate Changelog — Claude Code Skill

A Claude Code skill that generates a structured `CHANGELOG.md` from your git history, auto-categorizing commits into Added / Fixed / Changed / Removed sections.

## Install (3 steps)

1. Copy the skill file:
   ```bash
   cp generate-changelog.md ~/.claude/skills/generate-changelog.md
   ```

2. Use it in Claude Code:
   ```
   /generate-changelog
   ```

3. That's it. The skill reads your git log and writes `CHANGELOG.md`.

## What It Does

- Finds the last git tag as the starting point
- Fetches all commits since that tag
- Auto-categorizes by commit message prefix:
  - `feat:`, `add:` → **Added**
  - `fix:`, `bug:` → **Fixed**
  - `refactor:`, `update:`, `chore:` → **Changed**
  - `remove:`, `delete:` → **Removed**
- Strips conventional commit prefixes for clean output
- Skips empty sections
- Preserves existing changelog entries

## Sample Output

```markdown
# Changelog

## [v1.2.0 → Unreleased] - 2026-03-29

### Added
- User authentication with OAuth2
- Dark mode toggle in settings

### Fixed
- Token refresh loop on expired sessions
- Missing validation on email field

### Changed
- Upgrade Next.js from 14 to 15
- Refactor database connection pooling
```
