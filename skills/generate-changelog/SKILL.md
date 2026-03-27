# Generate Changelog Skill

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

```
/generate-changelog
```

Or run directly:
```bash
bash skills/generate-changelog/scripts/generate-changelog.sh
```

## What it does

1. Fetches all commits since the last git tag (or from the beginning if no tags exist)
2. Auto-categorizes commits into: `Added` / `Fixed` / `Changed` / `Removed`
3. Outputs a properly formatted `CHANGELOG.md`

## Commit Convention

This tool works best with [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` → Added
- `fix:` → Fixed
- `refactor:`, `perf:`, `chore:` → Changed
- `remove:`, `deprecate:` → Removed

## Setup

1. Copy `skills/generate-changelog/scripts/generate-changelog.sh` to your project
2. Make it executable: `chmod +x generate-changelog.sh`
3. Run: `./generate-changelog.sh`

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New feature X

### Fixed
- Bug in Y

### Changed
- Improved Z

### Removed
- Deprecated W

## [v1.0.0] - 2026-03-27

### Added
- Initial release
```

## Requirements

- Git
- Bash 4.0+
- `gittag` command (optional, for version detection)