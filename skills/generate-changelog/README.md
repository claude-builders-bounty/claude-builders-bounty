# Claude Code CHANGELOG Generator Skill

This skill automatically generates a structured `CHANGELOG.md` from a project's git history.

## Installation

1. Copy `SKILL.md` to `~/.claude/skills/generate-changelog/SKILL.md`
2. Run: `/generate-changelog` in any git repository

That's it!

## Usage

```
/generate-changelog
```

The skill will:
- Fetch all commits since the last git tag
- Auto-categorize into: `Added` / `Fixed` / `Changed` / `Removed`
- Output a properly formatted `CHANGELOG.md`

## Example Output

```markdown
## [Unreleased]

### Added
- New feature for automated changelog generation
- Support for conventional commits parsing

### Fixed
- Bug in date formatting
- Memory leak in commit parsing

### Changed
- Improved performance of git log fetching
- Updated dependencies to latest versions

### Removed
- Deprecated legacy API endpoints
```

## Requirements
- Git installed
- At least one tag in the repository (optional - will process all commits if no tags exist)

## License
MIT