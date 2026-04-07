# 📜 CHANGELOG Generator - SKILL.md for Claude Code

## Overview

A Claude Code skill that generates structured CHANGELOG.md from git history.

## Installation

```bash
# Copy skill file to Claude Code skills directory
cp CHANGELOG_SKILL.md ~/.claude/skills/generate-changelog/SKILL.md
```

## Commands

### /generate-changelog

Generates a structured CHANGELOG.md from git history.

**Usage:**
```
/generate-changelog
```

**What it does:**
1. Fetches commits since the last git tag
2. Auto-categorizes into: Added / Fixed / Changed / Removed
3. Outputs a properly formatted CHANGELOG.md

**Categories:**
- **Added**: New features (feat, add, implement, new)
- **Fixed**: Bug fixes (fix, bugfix, repair, resolve)
- **Changed**: Updates and improvements (update, change, refactor)
- **Removed**: Deleted features (remove, delete, drop)

## Example

Before:
```
commit history:
- feat: add user authentication
- fix: resolve login bug
- update: improve documentation
```

After (CHANGELOG.md):
```markdown
# Changelog

## [v1.2.3] - 2026-03-29

### Added
- add user authentication (abc1234)

### Fixed
- resolve login bug (def5678)

### Changed
- improve documentation (ghi9012)
```

## Requirements

- Git repository
- At least one commit

## Output

Creates/updates `CHANGELOG.md` in the current directory.
