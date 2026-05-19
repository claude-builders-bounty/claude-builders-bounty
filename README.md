# changelog.sh / changelog.py

Generate a structured **CHANGELOG.md** from your project's git history.

## Quick Start

```bash
# 3 steps:
1. Copy changelog.py (or changelog.sh) to your project root
2. Run it:
   python changelog.py
3. CHANGELOG.md is ready — review and commit!
```

## Features

- ✅ Works via `python changelog.py` or `bash changelog.sh`
- ✅ Fetches commits since the last git tag (or initial commit if no tags)
- ✅ Auto-categorizes into: ✨ Added / 🐛 Fixed / 🔄 Changed / 🗑️ Removed / 📦 Other
- ✅ Follows [Conventional Commits](https://www.conventionalcommits.org/) format
- ✅ Generates proper commit links to GitHub/GitLab
- ✅ Fully tested on real repositories

## Usage

```bash
# Generate CHANGELOG.md
python changelog.py

# Preview to stdout
python changelog.py --preview

# Specify a starting tag
python changelog.py --since v1.0.0

# Specify repo URL for commit links
python changelog.py --repo my-user/my-project

# Custom output file
python changelog.py --output docs/CHANGELOG.md

# Bash version (same options)
bash changelog.sh --preview
```

## Sample Output

```markdown
# Changelog

## [2026.05.19] - 2026-05-19

_Generated from 12 commits since v1.0.0._

### ✨ Added

- feat: add payment webhook handler ([a1b2c3d](https://github.com/user/repo/commit/a1b2c3d))
- add user profile API endpoint ([e4f5g6h](https://github.com/user/repo/commit/e4f5g6h))

### 🐛 Fixed

- fix: resolve timeout in batch processing ([b7c8d9e](https://github.com/user/repo/commit/b7c8d9e))

### 🔄 Changed

- refactor: extract auth middleware ([f0g1h2i](https://github.com/user/repo/commit/f0g1h2i))

### 🗑️ Removed

- remove deprecated v1 API routes ([j3k4l5m](https://github.com/user/repo/commit/j3k4l5m))
```

## Requirements

- **Python version**: Python 3.8+
- **Shell version**: Bash 4+ (no dependencies beyond standard Unix tools)
- Git repository with commit history

## License

MIT
