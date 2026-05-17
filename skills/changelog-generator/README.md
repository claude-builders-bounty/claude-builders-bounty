# Changelog Generator

Generate a structured `CHANGELOG.md` from git history with one command.

## Quick Install

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/ouzegba-lgtm/changelog-generator/main/changelog.py

# 2. Make executable
chmod +x changelog.py

# 3. Run
python3 changelog.py
```

## Usage

```bash
# Basic: since last git tag
python3 changelog.py

# From a specific tag
python3 changelog.py --since v1.0.0

# Custom output path
python3 changelog.py --output docs/CHANGELOG.md

# From the very first commit
python3 changelog.py --since $(git rev-list --max-parents=0 HEAD)
```

## Features

- ✅ Fetches commits since the last git tag
- ✅ Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- ✅ Respects [Conventional Commits](https://www.conventionalcommits.org/) format
- ✅ Fallback keyword detection for non-conventional commits
- ✅ Includes commit SHA and author
- ✅ Appends to existing CHANGELOG.md (doesn't overwrite)
- ✅ Zero dependencies — Python 3.6+

## How It Works

1. Finds the most recent git tag via `git describe --tags`
2. Fetches all commits since that tag
3. Parses each commit message:
   - `feat:` / `add:` → **Added**
   - `fix:` / `bug:` → **Fixed**
   - `refactor:` / `update:` → **Changed**
   - `remove:` / `delete:` → **Removed**
   - `docs:` → **Documentation**
   - `test:` → **Tests**
   - `chore:` / `ci:` → **Chores**
4. Keyword fallback for non-standard messages
5. Outputs formatted Markdown to `CHANGELOG.md`

## Sample Output

```markdown
# Changelog

## [2026-05-17] — since v1.2.0

### Added
- New user dashboard with analytics (a1b2c3d, Alice)
- API endpoint for batch operations (e4f5g6h, Bob)

### Fixed
- Memory leak in WebSocket handler (i7j8k9l, Charlie)
- Race condition on login page (m0n1o2p, Alice)

### Changed
- Updated dependencies to latest versions (q3r4s5t, Bob)
- Refactored auth module for better testability (u6v7w8x, Charlie)
```

## Requirements

- Python 3.6+
- Git repository with at least one commit
