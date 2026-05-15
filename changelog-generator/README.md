# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. **Copy `changelog.py`** into your project root
2. **Run it** → `python3 changelog.py`
3. **Done** → `CHANGELOG.md` appears in your project

For different output: `python3 changelog.py --since v1.0.0 --output RELEASE.md`

## Requirements

- Python 3.8+ (stdlib only — no pip install needed)
- git

## Features

- **Zero dependencies** — uses only Python stdlib
- **Conventional Commits parsing** — `feat:`, `fix:`, `docs:`, `refactor:`, `chore:` etc.
- **Auto-categorization** — Added / Fixed / Changed / Removed
- **Tag-aware** — groups commits by git tags, puts untagged commits under Unreleased
- **Scope grouping** — when multiple scopes exist, groups them automatically
- **Emoji headers** — ✨ Added · 🐛 Fixed · 🔄 Changed · 🗑️ Removed
