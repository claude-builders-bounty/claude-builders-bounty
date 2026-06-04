---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history with auto-categorization
---

# CHANGELOG Generator

Generates a beautiful, structured `CHANGELOG.md` from your project's git history using conventional commit messages. Works as a Claude Code skill, standalone bash script, or Python script.

## Usage

In Claude Code, type:

> /generate-changelog

Or run directly from the terminal:

```bash
# Default — writes to CHANGELOG.md
bash scripts/generate-changelog.sh

# Print to stdout instead
bash scripts/generate-changelog.sh --stdout

# Disable emoji (plain text)
bash scripts/generate-changelog.sh --no-emoji

# Or use Python (more portable)
python scripts/generate_changelog.py
python scripts/generate_changelog.py --stdout
```

## Output Example

```markdown
# Changelog

## [Unreleased]

### 🚀 Added
- New user dashboard (`a1b2c3d`)
- Export to PDF feature (`e4f5g6h`)

### 🐛 Fixed
- Login redirect loop (`i7j8k9l`)
- Null pointer in profile page (`m0n1o2p`)
```

## Categories

| Category | Conventional Commit Types |
|----------|--------------------------|
| 🚀 Added | `feat`, `feature` |
| 🐛 Fixed | `fix`, `bugfix`, `hotfix` |
| 🔧 Changed | `refactor`, `style`, `chore` |
| 🔥 Removed | `revert`, `remove`, `deprecate` |
| 📖 Documentation | `docs`, `documentation` |
| ⚡ Performance | `perf`, `performance` |
| 🧪 Testing | `test`, `testing` |
| 🔒 Security | `security` |
| 📦 Dependencies | `deps`, `build`, `ci` |
| 🔮 Miscellaneous | (anything else) |

## Files

- `scripts/generate-changelog.sh` — Bash implementation (zero deps)
- `scripts/generate_changelog.py` — Python implementation (zero deps)
- `.github/workflows/generate-changelog.yml` — GitHub Action (automated releases)

## Requirements

- **git** 2.0+ (both versions)
- **bash** 4+ (bash version) or **python** 3.6+ (Python version)
