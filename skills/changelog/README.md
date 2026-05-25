# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from git history — works as a Claude Code skill or standalone bash script.

## Setup (2 steps)

1. **Copy the skill** into your project:
   ```bash
   cp -r skills/changelog/ your-project/skills/changelog/
   ```

2. **Run it**:
   ```bash
   bash skills/changelog/changelog.sh
   ```
   Or inside Claude Code: `/generate-changelog`

## How It Works

- Detects the most recent git tag (or uses initial commit)
- Categorizes commits into: Added, Fixed, Changed, Removed, Documentation, Tests, Performance, Security, Style, CI/CD
- Writes a clean, structured `CHANGELOG.md`

## Requirements

- `bash` (>= 4.0)
- `git`
- No other dependencies

## Sample Output

```markdown
# Changelog

## [v1.0.0] — 2026-05-25

### Added
- `feat: add changelog generation script (abc1234)`
- `feat: add conventional commit parsing (def5678)`

### Fixed
- `fix: handle missing git tags gracefully (ghi9012)`

### Changed
- `refactor: simplify output formatting (jkl3456)`
```

## Bounty

Part of [Bounty #1 — $50](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).
