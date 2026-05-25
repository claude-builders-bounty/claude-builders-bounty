# Changelog Generator

Generate a structured `CHANGELOG.md` from git history.

## Usage (3 steps)

```bash
# 1. Copy to your project
cp scripts/changelog.sh /path/to/your/project/

# 2. Generate changelog
cd /path/to/your/project
bash scripts/changelog.sh --since v1.0.0 --tag v1.1.0 --write

# 3. Done! CHANGELOG.md is created
```

## Features
- Auto-categorizes: Added / Fixed / Changed / Removed / Deprecated / Security
- Supports conventional commits (`feat:`, `fix:`, `refactor:`)
- Markdown with commit links
- Safe to run multiple times (prepend mode)

## Options

| Option | Description |
|--------|-------------|
| `--since v1.0.0` | Start from tag/ref |
| `--tag v1.1.0` | Version in header |
| `--write` | Write to CHANGELOG.md |
| `--output FILE` | Write to specific file |

## Sample

```markdown
# Changelog

## [v1.1.0] - 2026-05-25

### Added
- New search bar component ([abc1234])

### Fixed
- Login redirect loop ([def5678])

### Changed
- Upgraded dependencies ([ghi9012])

---
*14 changes in this release*
```
