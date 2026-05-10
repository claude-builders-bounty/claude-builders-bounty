# Generate Changelog 📋

A bash script that auto-generates a structured `CHANGELOG.md` from git history.

## Quick Start

```bash
# 1. Clone or copy changelog.sh into your repo
# 2. Run it
bash changelog.sh

# 3. Check CHANGELOG.md
```

## Features

- 🏷️ **Auto-categorization** — Commits sorted into Added, Fixed, Changed, Removed, etc.
- 🏷️ **Tag-aware** — Automatically detects the latest tag as starting point
- 🔗 **Commit links** — Each entry includes the short commit hash
- 📝 **Conventional commits** — Recognizes `feat:`, `fix:`, `refactor:`, etc.
- 🔍 **Keyword detection** — Also catches natural language patterns
- 📎 **Append mode** — Add new entries without overwriting existing changelog

## Usage

```bash
# Since last tag
bash changelog.sh

# Specific range
bash changelog.sh v1.0.0..v1.1.0

# Append to existing
bash changelog.sh --append

# Custom output
bash changelog.sh --output RELEASES.md
```

## Commit Classification

| Prefix/Keyword | Category |
|----------------|----------|
| `feat:`, `add`, `new`, `create`, `implement` | ✨ Added |
| `fix:`, `bug`, `patch`, `resolve`, `correct` | 🐛 Fixed |
| `refactor:`, `update:`, `change:`, `improve` | 🔄 Changed |
| `remove:`, `delete:`, `deprecate:`, `drop` | 🗑️ Removed |
| `docs:`, `readme` | 📚 Documentation |
| `chore:`, `ci:`, `build:`, `test:` | 🔧 Maintenance |

## Requirements

- Bash 4.0+
- Git repository

## License

MIT
