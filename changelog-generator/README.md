# Git Changelog Generator 📝

Generate structured `CHANGELOG.md` files from Git conventional commits, auto-categorized into **Added / Fixed / Changed / Removed**.

## Features

- **Conventional Commits** — Parses `feat:`, `fix:`, `docs:`, etc.
- **4 categories** — Added, Fixed, Changed, Removed
- **Dual implementation** — Bash script (lightweight) + Python script (full-featured)
- **Flexible ranges** — Full history, between tags, or unreleased only
- **Zero dependencies** — Only requires `git`

## Setup (3 steps)

```bash
# 1. Copy the script to your project
cp generate-changelog.sh your-project/scripts/

# 2. Make it executable
chmod +x your-project/scripts/generate-changelog.sh

# 3. Run it
cd your-project && ./scripts/generate-changelog.sh
```

Or use the Python version:

```bash
cp generate-changelog.py your-project/scripts/
python3 your-project/scripts/generate-changelog.py
```

## Usage

### Bash

```bash
# Full changelog
./generate-changelog.sh

# Since a specific tag
./generate-changelog.sh --since v1.0.0

# Unreleased changes only
./generate-changelog.sh --unreleased

# Write to file
./generate-changelog.sh -o CHANGELOG.md
```

### Python

```bash
python3 generate-changelog.py
python3 generate-changelog.py --since v1.0.0
python3 generate-changelog.py --unreleased
python3 generate-changelog.py -o CHANGELOG.md
```

## Category Mapping

Conventional commit types are mapped to changelog categories:

| Commit Type | Category |
|-------------|----------|
| `feat` | **Added** |
| `fix` | **Fixed** |
| `remove` | **Removed** |
| `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert` | **Changed** |
| (non-conventional) | **Changed** |

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-05-01

### Added

- **auth:** add OAuth2 support (`d4e5f6a`)
- **dashboard:** add real-time charts (`b7c8d9e`)

### Fixed

- **db:** fix connection pool leak (`f0a1b2c`)

### Changed

- upgrade dependencies (`a1b2c3d`)
```

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>
```

Examples:
```
feat(auth): add OAuth2 support
fix(db): fix connection pool leak
docs: update README
remove: drop deprecated API endpoint
```

## Requirements

- **Bash version:** 3.2+ (compatible with macOS default bash)
- **Python version:** Python 3.9+
- **Git:** Any modern version

## License

MIT
