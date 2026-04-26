# Changelog Generator Skill

Generate structured CHANGELOG.md from git history with automatic categorization.

## Setup

```bash
cd skills/changelog-generator
chmod +x changelog.sh
```

## Usage

```bash
# Generate CHANGELOG.md in current directory
./changelog.sh

# Generate to specific file
./changelog.sh my-changelog.md
```

## Features

- ✅ Fetches commits since last git tag
- ✅ Auto-categorizes: Added / Fixed / Changed / Removed
- ✅ Follows Keep a Changelog format
- ✅ Works with conventional commits
- ✅ Fallback categorization for non-conventional commits

## Categories

| Pattern | Category |
|---------|----------|
| `feat:`, `add`, `implement` | Added |
| `fix:`, `bugfix`, `hotfix` | Fixed |
| `refactor:`, `update`, `improve` | Changed |
| `remove:`, `delete`, `drop` | Removed |

## Example Output

```markdown
# Changelog

## [Unreleased] - 2026-04-26

### Added
- New authentication system
- Dark mode support

### Fixed
- Login page redirect bug
```
