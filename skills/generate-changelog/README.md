# Generate CHANGELOG Skill

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from git history.

## Setup

1. Copy the `skills/generate-changelog` folder to your Claude Code skills directory
2. Make the script executable: `chmod +x changelog.sh`

## Usage

### Option 1: Claude Code Command
```
/generate-changelog
```

### Option 2: Bash Script
```bash
./skills/generate-changelog/changelog.sh [version]
```

Example:
```bash
./changelog.sh v1.2.0
```

## Features

- ✅ Fetches commits since the last git tag
- ✅ Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed` / `Security`
- ✅ Outputs properly formatted `CHANGELOG.md`
- ✅ Follows [Keep a Changelog](https://keepachangelog.com/) format
- ✅ Supports conventional commits

## Sample Output

```markdown
# Changelog

## [v1.0.0] - 2026-05-19

### Added
- feat: initial README with bounty board
- feat: add pre-tool-use hook

### Changed
- Initial commit
```

## Categorization

| Category | Keywords |
|----------|----------|
| Added | feat, add, new, create, implement |
| Fixed | fix, bug, patch, resolve |
| Changed | change, update, modify, refactor |
| Removed | remove, delete, drop |
| Security | security, vulnerability, cve |

---

*Bounty #1 Implementation*
