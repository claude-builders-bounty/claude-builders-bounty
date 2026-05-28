# Changelog Generator

Generate structured `CHANGELOG.md` from git history in one command.

## Quick Start

```bash
# 1. Copy script to your project
cp changelog.sh ~/your-project/

# 2. Make executable
chmod +x changelog.sh

# 3. Run
bash changelog.sh
```

That's it! A `CHANGELOG.md` appears with commits auto-categorized into **Added**, **Fixed**, **Changed**, **Removed**.

## Usage

```bash
# Default: since last git tag → CHANGELOG.md
bash changelog.sh

# Custom starting point
bash changelog.sh v1.0.0

# Custom output file
bash changelog.sh v1.0.0 docs/CHANGELOG.md

# From first commit (no tags)
bash changelog.sh HEAD~50
```

## Features

- 🔍 Reads git log since last tag (or custom ref)
- 🏷️ Auto-categorizes commits by conventional commit prefix (`feat:`, `fix:`, etc.)
- 📝 Falls back to keyword detection for non-conventional commits
- ⚡ Single bash script — no dependencies beyond git
- 📅 Includes version and date headers

## Example Output

```markdown
# Changelog

## [v2.1.0] - 2026-05-27

### Added
- User authentication with OAuth2
- Dark mode toggle in settings
- Export reports to PDF

### Fixed
- Login redirect loop on Safari
- Dashboard loading spinner stuck

### Changed
- Updated API rate limit from 100 to 500/min
- Refactored notification service

### Removed
- Legacy v1 API endpoints
```

## Tested On

- Git repos with tags (conventional commits)
- Git repos without tags (uses `--max-parents=0`)
- Monorepos with thousands of commits
