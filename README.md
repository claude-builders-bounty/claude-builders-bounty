# Changelog Generator

A bash script to automatically generate a structured `CHANGELOG.md` from git history.

## Features

- Fetches commits since the last git tag (or all commits if no tags exist)
- Auto-categorizes commits into: `Added` / `Fixed` / `Changed` / `Removed`
- Outputs a properly formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format
- Supports conventional commit messages (e.g., `feat:`, `fix:`, `refactor:`, `remove:`)

## Quick Start (3 Steps)

```bash
# 1. Copy the script to your project
curl -O https://raw.githubusercontent.com/your-repo/main/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Generate your changelog
./changelog.sh
```

## Usage

```bash
# Generate from last tag to HEAD (default)
./changelog.sh

# Generate since a specific tag
./changelog.sh --since v1.0.0

# Custom output file
./changelog.sh --output CHANGES.md

# Preview without writing to file
./changelog.sh --dry-run

# Show help
./changelog.sh --help
```

## Commit Message Convention

The script categorizes commits based on conventional commit prefixes:

| Prefix | Category |
|--------|----------|
| `feat:`, `feature:`, `add:` | **Added** |
| `fix:`, `bug:`, `bugfix:`, `hotfix:` | **Fixed** |
| `refactor:`, `change:`, `update:`, `modify:` | **Changed** |
| `remove:`, `delete:`, `rm:` | **Removed** |

Commits without recognized prefixes are categorized by keyword matching in the description, or placed in **Other**.

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2026-09-22] - since v1.0.0

### Added
- add new feature

### Fixed
- resolve critical bug

### Changed
- improve code structure

### Removed
- delete unused test file
```

## Requirements

- Bash 4.0+ (for associative arrays)
- Git

## License

MIT