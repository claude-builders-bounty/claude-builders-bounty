# Bounty #1: Structured CHANGELOG Generator

Generate a beautiful, [Keep-a-Changelog](https://keepachangelog.com/) formatted `CHANGELOG.md` directly from your git history.

## Setup (3 Steps)

```bash
# 1. Clone or download this directory
cp -r bounty-1/ /path/to/your/project/

# 2. Run the script
cd /path/to/your/project
bash bounty-1/changelog.sh

# 3. Done! Check your shiny new CHANGELOG.md
cat CHANGELOG.md
```

## Usage

```bash
# Generate for current directory
bash changelog.sh

# Generate for another repo
bash changelog.sh /path/to/repo
```

## How It Works

1. **Detects range** — uses the latest git tag as baseline (or all commits if no tags)
2. **Parses prefixes** — `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `remove:`, etc.
3. **Keyword fallback** — scans for words like "add", "fix", "remove" when no prefix is present
4. **Outputs CHANGELOG.md** — standard sections: Added, Fixed, Changed, Removed

## Supported Prefixes

| Prefix | Category |
|--------|----------|
| `feat:`, `feature:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `chore:`, `refactor:`, `perf:`, `ci:`, `build:` | Changed |
| `docs:`, `doc:` | Changed |
| `remove:`, `delete:`, `revert:` | Removed |

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2026-04-09

### Added

- dark mode toggle
- user profile avatars
- export to CSV feature

### Fixed

- login redirect loop
- timezone offset in scheduler

### Changed

- upgraded dependencies to latest
- improved search indexing performance

### Removed

- deprecated v1 API endpoints

---

_Generated from 23 commits since v1.1.0._
```

## Requirements

- Bash 4.0+
- Git
