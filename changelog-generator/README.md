# CHANGELOG Generator

Generate a structured CHANGELOG.md from your git history automatically.

## Quick Start (3 Steps)

### Step 1: Download
```bash
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.sh
chmod +x changelog.sh
```

### Step 2: Run
```bash
./changelog.sh
```

### Step 3: Done!
Check the generated `CHANGELOG.md` file in your project root.

---

## Features

- ✅ Auto-categorizes commits into: **Added** / **Fixed** / **Changed** / **Removed**
- ✅ Fetches commits since the last git tag
- ✅ Outputs properly formatted CHANGELOG.md
- ✅ Works with any git repository

## Advanced Usage

```bash
# Custom output file
./changelog.sh docs/CHANGELOG.md

# Run in specific directory
cd /path/to/project && ./changelog.sh
```

## How It Works

1. Detects the last git tag (or uses all commits if no tags)
2. Analyzes commit messages using keyword matching:
   - **Added**: add, create, implement, new, feat, feature, initial
   - **Fixed**: fix, bug, patch, resolve, repair, correct
   - **Changed**: change, update, modify, refactor, improve, enhance, style, docs, test
   - **Removed**: remove, delete, drop, deprecate, eliminate
3. Generates a structured CHANGELOG.md

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2026-03-28

### Added
- New user authentication system
- Dark mode support

### Fixed
- Memory leak in data processing
- Crash on startup for Windows users

### Changed
- Updated dependencies to latest versions
- Refactored API response handling

### Removed
- Deprecated legacy login endpoint
```

## License

MIT
