# CHANGELOG Generator

Auto-generate a structured `CHANGELOG.md` from git history.  
**Bounty: $50** — [#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

## Setup (3 steps)

```bash
# 1. Copy the script
cp changelog.py /usr/local/bin/generate-changelog
chmod +x /usr/local/bin/generate-changelog

# 2. Run in any git repo
cd /path/to/your-project
generate-changelog

# 3. Output appears as CHANGELOG.md
```

## Usage

```bash
# Basic: generate CHANGELOG.md in current directory
python changelog.py

# Custom repo path
python changelog.py --repo /path/to/repo

# Custom output file
python changelog.py --output docs/CHANGELOG.md
```

## Features
- Fetches commits since the last git tag
- Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
- Uses conventional commit patterns (feat:, fix:, add, remove, etc.)
- Falls back to "Unreleased" if no tags exist
- Works on any git repository — no dependencies beyond Python 3

## Sample Output
```markdown
# Changelog

## [v1.2.0] - 2026-06-30

### Added
- Add dark mode toggle with localStorage persistence (abc12345)
- Introduce ClawChat real-time collaboration (def67890)

### Fixed  
- Fix memory leak in WebSocket handler (ghi11121)
- Bug: login redirect loop on expired session (jkl31415)

### Changed
- Update dependencies to latest stable versions (mno16171)
- Refactor auth middleware for better error handling (pqr81920)
```