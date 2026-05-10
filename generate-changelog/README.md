# generate-changelog

A Claude Code skill + Python script that generates a structured `CHANGELOG.md` from git history.

## Features

- ✅ Auto-categorizes commits into **Added** / **Fixed** / **Changed** / **Removed**
- ✅ Detects **conventional commit** prefixes (`feat:`, `fix:`, `refactor:`, etc.)
- ✅ Keyword-based fallback for non-conventional commits
- ✅ **Tag-aware**: auto-detects the latest git tag, fetches commits since then
- ✅ **Append mode**: prepends new entries to existing CHANGELOG.md
- ✅ **Scope grouping**: groups entries by conventional commit scope
- ✅ **BREAKING CHANGE** detection with ⚠️ markers
- ✅ PR/issue number extraction and linking
- ✅ Zero dependencies (Python 3.7+ standard library only)
- ✅ Works on Windows, macOS, and Linux

## Setup (3 steps)

```bash
# 1. Copy the script to your project
cp -r generate-changelog/ /your/project/generate-changelog/

# 2. Run it
python3 generate-changelog/generate_changelog.py

# 3. Done! CHANGELOG.md is generated in your project root
```

## Usage

### As a Claude Code Skill

```
/generate-changelog
/generate-changelog --from v1.0.0 --to v2.0.0
```

### As a Python Script

```bash
# Basic: from last tag to HEAD
python3 generate-changelog/generate_changelog.py

# Custom range
python3 generate-changelog/generate_changelog.py --from v1.0.0 --to v2.0.0

# Full history (no tags yet)
python3 generate-changelog/generate_changelog.py --from "" --output CHANGELOG.md

# Append to existing changelog
python3 generate-changelog/generate_changelog.py --append

# Include chore/docs/test commits
python3 generate-changelog/generate_changelog.py --all

# Group by scope
python3 generate-changelog/generate_changelog.py --scope
```

## Categorization Rules

| Pattern | Category |
|---------|----------|
| `feat:`, `add`, `new`, `implement` | **Added** |
| `fix:`, `bug`, `patch`, `resolve` | **Fixed** |
| `refactor:`, `change`, `update`, `improve`, `BREAKING CHANGE` | **Changed** |
| `remove:`, `delete`, `drop`, `deprecate` | **Removed** |
| `chore:`, `docs:`, `test:`, `ci:` | **Maintenance** (hidden unless `--all`) |

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-05-10

### Added
- Support for multi-region deployments (#42)
- New CLI command `config export` (#38)
- Implement dark mode toggle (#35)

### Fixed
- Crash on startup when config file is missing (#45)
- Memory leak in long-running sessions (#40)

### Changed
- ⚠️ **BREAKING**: `api.authenticate()` now requires `token` parameter (#44)
- Upgraded dependency `requests` from 2.28 to 2.31 (#41)

### Removed
- Deprecated `v1_compat` module (#39)
```

## License

MIT
