# Changelog Generator

Automatically generate a structured `CHANGELOG.md` from your project's git history.

## Setup

1. Copy `changelog.sh` to your project root
2. Run `bash changelog.sh`
3. Find your changelog in `CHANGELOG.md`

## Usage

### Bash Script

```bash
# Generate changelog from last tag
bash changelog.sh

# Generate changelog since a specific tag
bash changelog.sh --since v1.0.0

# Output to a different file
bash changelog.sh --output HISTORY.md
```

### Claude Code Skill

Copy `SKILL.md` to your project's `.claude/skills/` directory, then use:

```
/generate-changelog
```

## How It Works

The generator analyzes commit messages and auto-categorizes them:

| Prefix | Category |
|--------|----------|
| `feat`, `add`, `new`, `create`, `implement` | Added |
| `fix`, `bug`, `patch`, `resolve`, `close` | Fixed |
| `remove`, `delete`, `drop`, `deprecate` | Removed |
| Everything else | Changed |

## Output Format

Follows [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [v1.2.0] - 2026-05-16

### Added
- feat: Add user authentication
- new: Create dashboard component

### Fixed
- fix: Resolve login redirect issue

### Changed
- refactor: Update database schema
- docs: Improve API documentation
```

## License

MIT
