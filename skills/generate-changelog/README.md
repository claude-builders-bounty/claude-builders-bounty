# Generate Changelog

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from git history.

## Quick Start

### Option 1: Claude Code Skill

1. Copy `SKILL.md` to `~/.claude/skills/generate-changelog/SKILL.md`
2. Run: `/generate-changelog`

### Option 2: Bash Script

```bash
# Generate changelog
bash scripts/changelog.sh

# Custom output file
bash scripts/changelog.sh --output docs/CHANGELOG.md

# Preview without writing
bash scripts/changelog.sh --dry-run
```

## Features

- ✅ Auto-categorizes commits by type (Added/Fixed/Changed/Removed)
- ✅ Supports conventional commit prefixes
- ✅ Detects last git tag automatically
- ✅ Clean, readable output format
- ✅ Zero dependencies (pure bash)

## Commit Type Mapping

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `new:` | Added |
| `fix:`, `bugfix:`, `resolve:` | Fixed |
| `change:`, `refactor:`, `update:` | Changed |
| `remove:`, `delete:`, `drop:` | Removed |

## Example Output

```markdown
## [v1.2.0] - 2026-05-07

### Added
- feat: add user authentication system
- feat: implement password reset flow

### Fixed
- fix: resolve login timeout issue

### Changed
- refactor: optimize database queries
```

## License

MIT
