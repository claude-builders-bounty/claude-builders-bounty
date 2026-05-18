# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from your project's git history — automatically categorized by conventional commit types.

## Quick Start

```bash
# 1. Clone this repo or copy changelog.py into your project
# 2. Run it
python changelog.py

# 3. Check the output
cat CHANGELOG.md
```

## Usage

```bash
# Default: writes to CHANGELOG.md
python changelog.py

# Print to stdout (no file write)
python changelog.py --stdout

# Specify a different repo
python changelog.py --repo /path/to/project

# Start from a specific tag (default: last tag)
python changelog.py --since v1.0.0
```

## How It Works

1. Fetches all commits since the last git tag
2. Categorizes using [Conventional Commits](https://www.conventionalcommits.org/) prefixes (`feat:`, `fix:`, `chore:`, etc.)
3. Falls back to semantic keyword matching if no prefix found
4. Outputs a clean, structured `CHANGELOG.md`

### Categories

| Section     | Triggers |
|-------------|----------|
| **Added**   | `feat:`, `feature:`, `add:`, `new:` |
| **Fixed**   | `fix:`, `bug:`, `hotfix:`, `security:` |
| **Changed** | `refactor:`, `perf:`, `chore:`, `docs:`, `update:` |
| **Deprecated** | `deprecate:`, `deprecated:` |
| **Removed** | `remove:`, `delete:`, `drop:` |

## Requirements

- Python 3.8+
- Git repository with tags (optional — works without tags too)

## Sample Output

```markdown
# Changelog

## [v2.0.0] - 2025-06-15

### Added
- Add user authentication via OAuth2 (abc1234)
- New dashboard analytics widget (def5678)

### Fixed
- Fix memory leak in event listener (ghi9012)
- Resolve race condition on concurrent writes (jkl3456)

### Changed
- Refactor database layer for better performance (mno7890)
- Update dependency versions (pqr1234)
```
