# Claude CHANGELOG Generator

A Claude Code skill (or standalone bash script) that generates a structured `CHANGELOG.md` from git history.

## Features

- Fetches commits since the last git tag
- Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- Outputs properly formatted `CHANGELOG.md`
- Works with conventional commits

## Usage

### As a Claude Code Skill
```
/generate-changelog
```

### As a Bash Script
```bash
bash changelog.sh
```

### With Options
```bash
OUTPUT_FILE=RELEASE_NOTES.md REPO_DIR=/path/to/repo bash changelog.sh
```

## Commit Prefixes

The script automatically categorizes commits based on prefixes:

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `feature:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `change:`, `update:`, `refactor:`, `improve:` | Changed |
| `remove:`, `delete:`, `deprecate:` | Removed |

## Output Example

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-04-09

### Added
- New API endpoint for user authentication
- Support for dark mode

### Fixed
- Memory leak in image processing

### Changed
- Improved database query performance

### Removed
- Deprecated legacy API endpoints
```

## Requirements

- Bash shell
- Git

## Bounty

Created for [$50 Bounty #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).

## License

MIT
