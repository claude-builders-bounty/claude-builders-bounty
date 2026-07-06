# Changelog Generator

Generate a structured CHANGELOG.md from git history.

## Usage

```bash
# Basic usage (outputs to CHANGELOG.md)
./generate-changelog.sh

# Specify output file
./generate-changelog.sh --output docs/CHANGELOG.md

# Specify repo directory
./generate-changelog.sh --output CHANGELOG.md /path/to/repo
```

## Features

- Auto-categorizes commits into: Added, Fixed, Changed, Removed, Documentation, Dependencies
- Uses conventional commit prefixes (feat, fix, refactor, remove, docs, deps)
- Generates since last git tag (or first commit if no tags exist)
- Fully portable bash script — zero dependencies

## Installation

```bash
# Option 1: Download and run
curl -sL -o /usr/local/bin/generate-changelog \
  https://raw.githubusercontent.com/dev-nana27/changelog-generator/main/generate-changelog.sh
chmod +x /usr/local/bin/generate-changelog

# Option 2: As a Claude Code command
# Add to CLAUDE.md: /generate-changelog = bash /path/to/generate-changelog.sh
```

## Conventional Commit Prefixes

| Category | Prefixes |
|----------|----------|
| Added | feat, add, feature |
| Fixed | fix, bug, hotfix, patch |
| Changed | refactor, perf, update, change, upgrade |
| Removed | remove, deprecate, delete, drop |
| Docs | docs, doc, readme |
| Dependencies | deps, depend, bump |

## Sample Output

```
# Changelog

## [Unreleased] - 2026-07-06

### Added
- feat: add user avatar upload support

### Fixed
- fix: resolve cache invalidation race condition

### Changed
- refactor: migrate from Express to Hono

---

**Total commits since v1.0.0: 12**
```

## License

MIT

