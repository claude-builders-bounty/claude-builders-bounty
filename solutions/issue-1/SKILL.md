# Generate CHANGELOG from Git History

A Claude Code skill that automatically generates a structured CHANGELOG.md from a project's git history.

## Usage

In Claude Code, type:
```
/generate-changelog
```

Or run directly:
```bash
bash changelog.sh
```

## What it does

1. Fetches all commits since the last git tag
2. Auto-categorizes changes into:
   - **Added** - New features
   - **Fixed** - Bug fixes
   - **Changed** - Modifications to existing features
   - **Removed** - Deprecated or removed features
3. Generates a properly formatted CHANGELOG.md

## Requirements

- Git installed
- At least one git tag in the repository
- Claude Code (for skill version)

## Installation

### Option 1: As Claude Code Skill

1. Copy `SKILL.md` to `~/.claude/skills/generate-changelog/`
2. Use `/generate-changelog` command in any project

### Option 2: As Standalone Script

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/YOUR_FORK/claude-builders-bounty/main/solutions/issue-1/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it
./changelog.sh
```

## Configuration

Edit the script to customize:
- `CATEGORIES` - Change commit categorization keywords
- `OUTPUT_FILE` - Change output filename
- `INCLUDE_HASHES` - Include/exclude commit hashes

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2026-03-27

### Added
- Add user authentication system
- Add password reset functionality
- Add email notifications

### Fixed
- Fix login redirect bug
- Fix timezone issue in dashboard

### Changed
- Improve search performance
- Update dependencies to latest versions

### Removed
- Remove deprecated API endpoints
- Remove legacy database migration scripts

## [v1.1.0] - 2026-03-20

### Added
- Initial release
```

## Categorization Rules

Commits are categorized based on keywords:

| Category | Keywords |
|----------|----------|
| Added | `add`, `new`, `feature`, `implement`, `create`, `introduce` |
| Fixed | `fix`, `bug`, `patch`, `resolve`, `correct`, `repair` |
| Changed | `change`, `update`, `modify`, `improve`, `refactor`, `enhance` |
| Removed | `remove`, `delete`, `deprecate`, `drop`, `eliminate` |

## License

MIT

## Credits

Created for claude-builders-bounty Issue #1
