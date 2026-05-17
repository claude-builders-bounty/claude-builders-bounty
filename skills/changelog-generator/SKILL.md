# SKILL.md — /generate-changelog

## Description
Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage
```
/generate-changelog --repo /path/to/repo --output CHANGELOG.md
```

## Options
- `--repo`: Path to the git repository (default: current directory)
- `--output`: Output file path (default: CHANGELOG.md)

## Features
- Fetches commits since the last git tag
- Auto-categorizes into: Added / Fixed / Changed / Removed / Documentation / Testing / Performance / Security
- Uses conventional commit prefixes for categorization
- Outputs properly formatted Markdown with commit SHA references
- Zero dependencies (stdlib only)

## Example Output
```markdown
# Changelog
_Generated: 2026-05-17_

## [v1.0.0] - 2026-05-17

### Added
- New user authentication flow (#123)

### Fixed
- Fix memory leak in cache handler (#456)

### Changed
- Update dependencies to latest versions
```

## Requirements
- Python 3.6+
- Git repository with commit history
