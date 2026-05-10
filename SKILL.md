---
name: changelog-generator
description: Generate structured CHANGELOG.md from git history with auto-categorization into Added/Fixed/Changed/Removed/Documentation/Security/Performance
---

# Changelog Generator

A Claude Code skill that generates well-structured `CHANGELOG.md` from your project's git history.

## Quick Start

```bash
# Generate changelog from latest tag to HEAD
/generate-changelog

# Generate from a specific tag
/generate-changelog --since v1.0.0

# Write to custom file
/generate-changelog --output docs/CHANGELOG.md
```

Or using bash/python directly:

```bash
bash changelog.sh
python3 changelog.py
```

## Features

- **Auto-categorization** — Commits are categorized into: 🚀 Added, 🐛 Fixed, 🔄 Changed, 🗑️ Removed, 📝 Documentation, 🔒 Security, ⚡ Performance
- **Smart prefix stripping** — Auto-removes `feat:`, `fix:`, `docs:`, etc. conventional commit prefixes
- **Tag-aware** — Uses latest git tag as version reference
- **Safe prepend** — Appends to existing CHANGELOG.md without overwriting
- **No dependencies** — Pure Python standard library + git CLI

## How It Works

1. Reads git log since the latest tag (or a specified reference)
2. Categorizes each commit by keyword matching
3. Outputs a formatted markdown file

## Requirements

- Git (any version)
- Python 3.10+
