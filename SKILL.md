---
name: changelog
version: 1.0.0
description: Generate structured CHANGELOG.md from git history
---

# generate-changelog

Generate a structured `CHANGELOG.md` from your project's git history.

## Usage

```
/generate-changelog [--since-tag v1.0.0] [--output CHANGELOG.md]
```

Or run directly:

```bash
bash changelog.sh
bash changelog.sh --since-tag v1.0.0
```

## What It Does

1. Reads commits since the last git tag (or beginning of history)
2. Auto-categorizes into: **Added / Fixed / Changed / Removed / Security**
3. Uses Conventional Commits format (`feat:`, `fix:`, etc.)
4. Outputs a properly formatted `CHANGELOG.md`

## Acceptance Criteria Met

- [x] Works via `/generate-changelog` command or `bash changelog.sh`
- [x] Fetches commits since the last git tag
- [x] Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] README with setup instructions in 3 steps or fewer (see below)

## Setup (3 steps)

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/wbobbynmworley/claude-builders-bounty/main/changelog.sh

# 2. Make executable
chmod +x changelog.sh

# 3. Run
./changelog.sh
```

## Sample Output

```
# Changelog

All notable changes to this project.

Generated on 2026-05-01 by `generate-changelog.sh`

---
## v1.0.0 (current)

### Added
  - feat: add user authentication (\`a3f8d2b\`)
  - feat: add dashboard view (\`b7c1e9f\`)

### Fixed
  - fix: resolve memory leak in worker (\`d4e2a8c\`)

---
_Auto-generated. Edit manually if needed._
```

## Requirements

- Git repository with commits
- Standard Unix tools (`bash`, `git`, `sed`)