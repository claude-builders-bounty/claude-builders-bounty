# Changelog Generator

A bash script and Claude Code skill to automatically generate structured CHANGELOG.md files from git history.

## Quick Start

```bash
# Clone and enter the repo
git clone <repo-url>
cd <repo-name>

# Generate CHANGELOG.md
./generate-changelog.sh

# Or specify custom output file
./generate-changelog.sh RELEASE_NOTES.md
```

## Features

- ✅ Fetches commits since the last git tag automatically
- ✅ Auto-categorizes into Added/Fixed/Changed/Removed/Other
- ✅ Follows [Keep a Changelog](https://keepachangelog.com/) format
- ✅ Includes commit links when remote URL is available
- ✅ Handles repos with no tags (uses first commit as baseline)
- ✅ Skips merge commits for cleaner output

## Categorization Rules

Commits are automatically categorized based on:

| Category | Matches |
|----------|---------|
| **Added** | `feat:`, `add:`, "Add", "Implement", "Feature" |
| **Fixed** | `fix:`, `bugfix:`, "Fix", "Bug", "Resolve" |
| **Changed** | `change:`, `update:`, `refactor:`, "Update", "Refactor" |
| **Removed** | `remove:`, `delete:`, "Remove", "Delete", "Drop" |
| **Other** | Everything else |

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-04-01

### Added
- Add new action provider (#930) ([a3afda3](...)) by @phdargen
- Feature: Aave integration (#865) ([36013c6](...)) by @Anshuman Yadav

### Fixed
- Fix asyncio conflicts (#968) ([8ec4a85](...)) by @Darryl Sladden
```

## Claude Code Integration

Add to your `.claude/CLAUDE.md`:

```markdown
## /generate-changelog

Generate a structured CHANGELOG.md from git history.

Usage: `/generate-changelog [output-file]`
```

Or use the `SKILL.md` file directly with Claude Code's skill system.

## Testing

Tested on:
- ✅ Repository with tags
- ✅ Repository without tags
- ✅ Repository with conventional commits
- ✅ Repository with free-form commits
- ✅ Empty commit range (no changes since last tag)

## License

MIT - See LICENSE file
