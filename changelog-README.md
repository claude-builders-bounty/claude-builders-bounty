# 📝 Changelog Generator — Claude Code Skill

Generate a structured `CHANGELOG.md` from git history, categorizing commits into Added / Fixed / Changed / Removed.

## Install (3 steps)

```bash
# 1. Download the script
curl -sL https://raw.githubusercontent.com/DrGalio/claude-builders-bounty/feature/changelog-skill/changelog.sh \
  -o changelog.sh && chmod +x changelog.sh

# 2. Run it
bash changelog.sh

# 3. Check the output
cat CHANGELOG.md
```

## Usage

```bash
# Default: writes CHANGELOG.md in current directory
bash changelog.sh

# Custom output path
bash changelog.sh docs/CHANGELOG.md
```

## How commits are categorized

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `added:`, `feature:` | Added |
| `fix:`, `fixed:`, `bugfix:`, `hotfix:` | Fixed |
| `chore:`, `refactor:`, `change:`, `update:`, `docs:`, `perf:`, `style:`, `ci:`, `build:` | Changed |
| `remove:`, `removed:`, `delete:`, `deleted:`, `deprecate:`, `deprecated:` | Removed |
| _(anything else)_ | Changed |

## Example output

```markdown
# Changelog

All notable changes to **my-project** since v0.1.0.

## Unreleased — 2026-03-27

### Added

- feat: add search functionality
- feat: implement dark mode

### Fixed

- fix: memory leak in worker thread

### Changed

- chore: bump version to 0.2.0
- Improved error handling in API layer
```

## Requirements

- bash 4+
- git
