# CHANGELOG Generator

A simple bash script that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Setup

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/foxyManTou/claude-builders-bounty/main/changelog.sh

# 2. Make it executable
chmod +x changelog.sh
```

## Usage

```bash
# Generate CHANGELOG.md in the current directory
bash changelog.sh

# Specify output file
bash changelog.sh CHANGELOG.md

# Specify repo directory
bash changelog.sh CHANGELOG.md /path/to/repo
```

## How It Works

1. Finds the last git tag (or first commit if no tags exist)
2. Fetches all commits since that tag
3. Auto-categorizes commits by conventional commit prefix:
   - `feat:`, `feature:`, `add:`, `implement:`, `create:`, `introduce:` → **Added**
   - `fix:`, `bugfix:`, `hotfix:`, `patch:`, `correct:`, `resolve:` → **Fixed**
   - `change:`, `update:`, `refactor:`, `improve:`, `migrate:`, `perf:`, `optimize:`, `style:` → **Changed**
   - `remove:`, `delete:`, `deprecate:`, `drop:` → **Removed**
   - Everything else → **Other**
4. Outputs a clean `CHANGELOG.md` with commit hashes and authors

## Sample Output

```
# Changelog

## [Unreleased] - 2026-07-07

### Added
- feat: add WebSocket support for real-time updates (#2bd8b5e) by @developer
- feat: implement rate limiting middleware (#f7d46ba) by @developer

### Fixed
- fix: correct pagination off-by-one error (#1150a86) by @developer
- fix: resolve token refresh race condition (#6e33888) by @developer

### Changed
- refactor: migrate from CommonJS to ESM (#6150e8d) by @developer

### Removed
- remove: deprecated v1 API endpoints (#9e9501b) by @developer
```

## Requirements

- `git` (installed by default on most systems)
- Bash 4+