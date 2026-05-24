# changelog.py — Changelog Generator from Git History

A lightweight Python script that automatically generates a structured CHANGELOG.md from your project's git history.

**Bounty:** [claude-builders-bounty issue #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1) — $50

## Setup

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/YOUR_USER/claude-builders-bounty/main/changelog/changelog.py

# 2. Run it (Python 3.7+ required)
python changelog.py
```

## Usage

```bash
# Generate CHANGELOG.md for current project
python changelog.py

# Specify output file
python changelog.py --output HISTORY.md

# Specify another project
python changelog.py --project-dir /path/to/project

# Use custom git path
GIT_CMD="/usr/local/bin/git" python changelog.py
```

## How it works

1. Finds the last git tag (or first commit if no tags exist)
2. Fetches all commits since that tag
3. Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed** based on [Conventional Commits](https://www.conventionalcommits.org/) prefixes
4. Outputs a properly formatted CHANGELOG.md

### Category rules

| Prefix | Category |
|--------|----------|
| `feat:`, `feature:`, `add:`, `new:`, `implement:`, `introduce:`, `create:` | Added |
| `fix:`, `bugfix:`, `bug:`, `patch:`, `hotfix:`, `correct:`, `resolve:` | Fixed |
| `change:`, `update:`, `refactor:`, `perf:`, `improve:`, `modify:`, `rewrite:`, `bump:`, `upgrade:`, `migrate:` | Changed |
| `remove:`, `delete:`, `drop:`, `deprecate:`, `cleanup:`, `retire:` | Removed |
| Everything else | Uncategorized |

Also supports scoped conventional commits: `feat(scope): message`, `fix(scope): message`, etc.

## Example output

```markdown
# Changelog

## [v1.2.0] - 2026-05-24

### Added

- Add user authentication flow (a1b2c3d)
- New API endpoint for profile updates (e4f5g6h)

### Fixed

- Fix login redirect loop (i7j8k9l)
- Correct date formatting in reports (m0n1o2p)

### Changed

- Refactor database connection pooling (q3r4s5t)
- Update dependencies to latest versions (u6v7w8x)
```

## Requirements

- Python 3.7+
- Git (installed and in PATH)
