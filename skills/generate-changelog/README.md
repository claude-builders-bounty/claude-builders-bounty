# Changelog Generator

Generate a structured `CHANGELOG.md` from your project's git history.

## Usage

**Option 1: Bash script**
```bash
bash changelog.sh
```

**Option 2: Claude Code skill**
```
/generate-changelog
```

## What it does

- Fetches commits since the last git tag (or all commits if no tags)
- Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- Outputs a properly formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format
- Prepends new entries to existing changelog (doesn't overwrite)

## Installation

1. Copy `changelog.sh` to your project root
2. Run `bash changelog.sh`

That's it! ✅

## Categories

| Pattern | Category |
|---------|----------|
| `feat:`, `add`, `new`, `create`, `implement`, `introduce` | **Added** |
| `fix:`, `bug`, `hotfix`, `patch`, `resolve`, `correct` | **Fixed** |
| `change:`, `update`, `refactor`, `improve`, `optimize`, `modify` | **Changed** |
| `remove:`, `delete`, `drop`, `deprecate` | **Removed** |

## Example Output

```markdown
# Changelog

## [v1.2.0] - 2026-08-21

### Added
- feat: user authentication system (john, 2026-08-20)

### Fixed
- fix: resolve memory leak in parser (jane, 2026-08-19)

### Changed
- refactor: optimize database queries (bob, 2026-08-18)
```

## Requirements

- Git repository with commit history
- Bash (macOS/Linux) or Git Bash (Windows)

## License

MIT
