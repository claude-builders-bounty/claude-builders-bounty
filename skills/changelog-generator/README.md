# CHANGELOG Generator

Claude Code skill for generating structured changelogs from git history.

## Setup (3 steps)

1. Copy this directory to your project
2. Make the script executable: `chmod +x scripts/changelog.sh`  
3. Run in Claude Code: `/generate-changelog`

## Requirements

- bash 4.0+
- git 2.0+

## Output

A properly formatted `CHANGELOG.md` with commits categorized by type:

| Category | Commit Prefixes |
|----------|----------------|
| Added | `feat:`, `feature:` |
| Fixed | `fix:`, `bugfix:`, `hotfix:` |
| Changed | `refactor:`, `style:`, `perf:`, `chore:`, `docs:`, `test:`, `ci:`, `build:` |
| Removed | `revert:`, `remove:` |

## Sample Output

```markdown
# Changelog

## [v1.2.0] - 2026-05-13

### Added
- feat: add changelog generator
- feat: support conventional commits

### Fixed
- fix: handle empty git tag history

### Changed
- refactor: improve categorization logic
```
