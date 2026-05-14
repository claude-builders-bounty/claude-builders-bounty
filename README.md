# Changelog Generator

A bash script that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Setup (2 steps)

```bash
# 1. Copy the script to your project
cp changelog.sh /path/to/your/project/

# 2. Run it
cd /path/to/your/project && bash changelog.sh
```

## Usage

```bash
# Generate changelog since last tag (default)
./changelog.sh

# Generate changelog since a specific tag
./changelog.sh --tag v1.0.0

# Dry run (print to stdout)
./changelog.sh --dry-run

# Custom output file
./changelog.sh --output RELEASES.md

# Point to a different repo
./changelog.sh --repo /path/to/repo
```

## How It Works

1. Finds the last git tag (or uses the one you specify)
2. Reads all commits between that tag and HEAD
3. Auto-categorizes commits using [Conventional Commits](https://www.conventionalcommits.org/) prefixes:
   - **Added**: `feat:`, `add:`, `feature:`
   - **Fixed**: `fix:`, `bug:`, `patch:`, `hotfix:`
   - **Changed**: `change:`, `update:`, `refactor:`, `rename:`
   - **Removed**: `remove:`, `delete:`, `deprecate:`
   - **Docs**: `doc:`, `docs:`, `readme:`
4. Outputs a properly formatted `CHANGELOG.md`
5. Prepends to existing changelog if one exists

## Sample Output

```markdown
# Changelog

## since v2.1.0 (2026-05-14)

### Added

- feat: add user authentication module (`a1b2c3d`)
- add export CSV functionality (`e4f5g6h`)

### Fixed

- fix: resolve login redirect loop (`i7j8k9l`)
- patch: handle empty email field (`m0n1o2p`)

### Changed

- refactor: simplify database connection pool (`q3r4s5t`)

### Removed

- deprecate: remove legacy API v1 endpoints (`u6v7w8x`)
```

## Requirements

- Bash 3.2+
- Git
