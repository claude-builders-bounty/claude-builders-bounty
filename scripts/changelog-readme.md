# Changelog Generator

A bash script that automatically generates a structured `CHANGELOG.md` from git history.

## Features

- **Auto-categorizes** commits into: `Added`, `Fixed`, `Changed`, `Removed`, `Deprecated`, `Security`
- **Conventional commit** aware (`feat:`, `fix:`, `refactor:`, etc.)
- **Keyword fallback** for non-standard commit messages
- **Prepend mode** — safe to run multiple times (appends to existing CHANGELOG)
- **Zero dependencies** — pure bash + git
- **Markdown output** with links to commit SHAs

## Usage

```bash
# Generate changelog from last git tag to HEAD
bash scripts/changelog.sh

# Write to CHANGELOG.md
bash scripts/changelog.sh --write

# Specify a version range
bash scripts/changelog.sh --since v1.0.0 --tag v1.1.0

# Last 10 commits
bash scripts/changelog.sh --since HEAD~10 --write

# See all options
bash scripts/changelog.sh --help
```

## Sample Output

```markdown
# Changelog

## [v1.1.0] - 2026-05-25

### Added
- New search bar component ([abc1234])
- Dark mode support ([def5678])

### Fixed
- Login redirect loop on expired tokens ([ghi9012])
- Memory leak in websocket handler ([jkl3456])

### Changed
- Upgraded dependencies to latest versions ([mno7890])

### Security
- Patched XSS vulnerability in user input ([pqr1234])

---
*14 changes in this release*
```

## Tested On

This project itself! Here's what `bash scripts/changelog.sh` produces:

_A sample run against this repository produced the output shown above._

## Requirements

- Bash 4+
- Git 2.0+
- No other dependencies
