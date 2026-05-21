# Generate Changelog Skill

A Claude Code skill that generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

```bash
# 1. Copy the skill directory into your project
cp -r skills/generate-changelog/ /path/to/your/project/skills/generate-changelog/

# 2. Run it
bash skills/generate-changelog/changelog.sh

# 3. Done — CHANGELOG.md is generated in your project root
```

## Usage

```bash
# Generate changelog since the last git tag
bash skills/generate-changelog/changelog.sh

# Generate changelog since a specific tag
bash skills/generate-changelog/changelog.sh v1.2.0

# Generate changelog for all history
bash skills/generate-changelog/changelog.sh --all

# Preview without writing to file
bash skills/generate-changelog/changelog.sh --dry-run
```

## Sample output

Tested on this repository:

```
# Changelog

## [Unreleased] - 2026-05-21

### Added
- feat: initial README with bounty board
- Initial commit
```

## Categorization

Commits are auto-categorized by prefix/keyword:

| Category | Keywords |
|----------|----------|
| Added | `feat:`, `add`, `new`, `initial`, `create`, `implement` |
| Fixed | `fix:`, `bug`, `patch`, `correct`, `resolve` |
| Changed | `update`, `refactor`, `move`, `rename` (or anything uncategorized) |
| Removed | `remove`, `delete`, `deprecate`, `drop` |

## Requirements

- Git
- Python 3 (for commit categorization)
- Bash

## License

MIT
