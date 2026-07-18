# changelog-generator — Claude Code Skill

Automatically generate a structured `CHANGELOG.md` from git history.

## Quick Start (3 steps)

### As Claude Code Skill
1. Copy `SKILL.md` to `~/.claude/skills/changelog-generator/SKILL.md`
2. In Claude Code, run: `/generate-changelog`
3. Find your `CHANGELOG.md` in the project root

### As Standalone Script
```bash
python3 changelog.py                      # Uses last tag → HEAD
python3 changelog.py --since v1.0.0       # From v1.0.0 → HEAD
python3 changelog.py --output HISTORI.md  # Custom output file
```

## Features
- ✅ Works on any git repo
- ✅ Auto-categorizes commits: Added / Fixed / Changed / Removed
- ✅ Supports conventional commits (`feat:`, `fix:`, `refactor:`, etc.)
- ✅ Extracts GitHub PR numbers from commit messages
- ✅ Detects breaking changes
- ✅ Zero dependencies (pure Python 3 + git)
- ✅ Cross-platform (Windows/Mac/Linux)

## Example Output
```markdown
# Changelog

## [Unreleased] — 2025-07-18

### Added
- New user dashboard with analytics charts (#42)

### Fixed
- Memory leak in WebSocket connection (#39)

### Changed
- Upgrade React from 17 to 18 (#40)

### Removed
- Deprecated v1 API endpoints (#50)
```

## Sample Output (tested on this repo)

See [SAMPLE_CHANGELOG.md](SAMPLE_CHANGELOG.md) for a real generated example.
