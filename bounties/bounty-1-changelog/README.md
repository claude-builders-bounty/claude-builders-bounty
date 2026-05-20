# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from your git history. Automatically categorizes commits into **Added**, **Fixed**, **Changed**, and **Removed** sections.

## Quick Start (3 steps)

```bash
# 1. Clone or copy changelog.sh into your repo
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/claude-builders-bounty/main/bounties/bounty-1-changelog/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Generate your changelog
./changelog.sh
```

That's it! Your `CHANGELOG.md` is ready.

## Usage

```bash
# Default: outputs to CHANGELOG.md
./changelog.sh

# Custom output file
./changelog.sh CUSTOM_CHANGELOG.md
```

## How It Works

The script reads your git history and categorizes commits based on [Conventional Commits](https://www.conventionalcommits.org/) prefixes:

| Prefix | Category |
|--------|----------|
| `feat:` | Added |
| `fix:` | Fixed |
| `chore:`, `refactor:`, `perf:`, `style:`, `docs:`, `build:`, `ci:`, `test:` | Changed |
| `remove:`, `delete:` | Removed |
| Other | Other |

If you have git tags, it only includes commits since the latest tag.

## Example Output

```markdown
# Changelog

## [v1.0.0] → Unreleased — 2026-05-21

### Added
- add user authentication
- implement dark mode

### Fixed
- resolve login bug
- fix memory leak in parser

### Changed
- update dependencies
- refactor database queries

### Removed
- delete deprecated API endpoint
```

## Requirements

- Git repository with commits
- Bash 4.0+

## Running Tests

```bash
chmod +x test_changelog.sh
./test_changelog.sh
```

## License

MIT
