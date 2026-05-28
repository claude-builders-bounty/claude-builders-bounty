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
python changelog.py             # auto-detects last tag, writes to stdout
python changelog.py --output CHANGELOG.md
python changelog.py --tag v1.0.0 --output CHANGELOG.md
python changelog.py --format json --output changelog.json
```

## Requirements
- Python 3.8+
- `git` installed and available in PATH
- Must be run within a git repository

## Setup (3 steps)
1. Copy `changelog.py` into your project
2. Run `python changelog.py --output CHANGELOG.md`
3. Commit the generated file

## Features
- ✅ Works via `/generate-changelog` command or `python changelog.py`
- ✅ Fetches commits since last git tag (auto-detected, or use `--tag`)
- ✅ Auto-categorizes into: Added / Fixed / Changed / Removed / Deprecated / Security
- ✅ Outputs properly formatted CHANGELOG.md
- ✅ Supports `--output` and `--tag` options
- ✅ Multiple formats: markdown, json, html
- ✅ Zero external dependencies (pure Python stdlib)
- ✅ Works on Linux, macOS, and Windows
