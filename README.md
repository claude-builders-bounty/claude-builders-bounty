# CHANGELOG Generator

A simple bash script that automatically generates a structured `CHANGELOG.md` from your git history using conventional commits.

## Quick Start

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/changelog-generator-skill/changelog.sh
chmod +x changelog.sh

# 2. Run it in your repository
./changelog.sh

# 3. Review the generated CHANGELOG.md
cat CHANGELOG.md
```

That's it! The script will automatically detect your latest git tag and generate a categorized changelog.

## Usage

```bash
# Basic usage - generates CHANGELOG.md from latest tag
./changelog.sh

# Custom output file
./changelog.sh --output docs/CHANGELOG.md

# Only include commits since a specific tag
./changelog.sh --since-tag v1.0.0

# Show help
./changelog.sh --help
```

## How It Works

The script parses your git history and categorizes commits based on conventional commit prefixes:

| Prefix | Category |
|--------|----------|
| `feat:`, `feature:`, `add:` | Added |
| `fix:`, `bugfix:`, `bug:` | Fixed |
| `chore:`, `refactor:`, `update:`, `change:` | Changed |
| `remove:`, `revert:`, `deprecate:` | Removed |
| `docs:`, `doc:` | Docs |
| Others | Miscellaneous |

## Conventional Commits

For best results, use conventional commit format:

```
feat: add new user authentication
fix: resolve login timeout issue
docs: update API documentation
chore: bump dependencies
```

The script extracts the message after the prefix and formats it nicely in the CHANGELOG.

## Output Format

Generates a [Keep a Changelog](https://keepachangelog.com/) compatible format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

---

## [1.0.0] - 2024-01-15

### Added

- Add new user authentication ([abc1234](https://github.com/user/repo/commit/abc1234))
- Add password reset flow

### Fixed

- Resolve login timeout issue ([def5678](https://github.com/user/repo/commit/def5678))

### Changed

- Bump dependencies

### Removed

- Deprecated legacy API endpoints
```

## Requirements

- Git
- Bash 4.0+

## License

MIT