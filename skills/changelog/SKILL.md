# `/generate-changelog` — Auto-generate CHANGELOG.md from git history

## Description
Generates a structured `CHANGELOG.md` from your project's git history since the last tag.
Categorizes commits into **Added**, **Fixed**, **Changed**, **Removed**, **Deprecated**, and **Security**.

## Usage

### As a Claude Code command
```
/generate-changelog
/generate-changelog --output CHANGELOG.md
/generate-changelog --tag v1.0.0
```

### As a standalone script
```bash
python changelog.py             # writes to CHANGELOG.md
python changelog.py --output docs/CHANGELOG.md
python changelog.py --tag v1.0.0 --output CHANGELOG.md
```

## Requirements
- Python 3.8+
- `git` installed and available in PATH
- Must be run within a git repository

## Setup
1. Copy `changelog.py` into your project
2. Run `python changelog.py`
3. Check the generated `CHANGELOG.md`

## Features
- Zero external dependencies (pure Python stdlib)
- Auto-fetches commits since last git tag
- Groups into Added/Fixed/Changed/Removed/Security
- Supports `--output` and `--tag` options
- Works on Linux, macOS, and Windows
