# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from git history. Auto-categorizes commits into
Added / Fixed / Changed / Removed using conventional commit prefixes.

## Setup (1 step)

```bash
chmod +x changelog.sh
```

## Usage

```bash
# Generate from last tag to HEAD
./changelog.sh

# Specify a starting tag
./changelog.sh --since v1.0.0

# Custom output path
./changelog.sh --output docs/CHANGELOG.md
```

## How It Works

1. Finds the most recent git tag
2. Collects all commits since that tag
3. Categorizes by prefix: `feat`/`add` → Added, `fix`/`bug` → Fixed, `remove`/`drop` → Removed
4. Outputs a Keep a Changelog-compatible `CHANGELOG.md`

## Sample Output

```markdown
# Changelog

## [v2.1.0] — 2026-06-06

### Added
- Support for dark mode
- Export to CSV feature

### Fixed
- Login redirect loop on Safari
- Memory leak in dashboard chart

### Changed
- Updated dependencies
- Refactored auth module

---
_12 commits since v2.0.0_
```
