---
name: generate-changelog
description: Automatically generates a structured, beautifully categorized CHANGELOG.md from git history with full Conventional Commits support.
---

# Generate Changelog Pro Skill

This skill equips Claude Code with a professional-grade `./changelog.sh` tool to automatically generate or incrementally update a beautifully formatted `CHANGELOG.md` in your repository root.

## Outstanding Features

- **Conventional Commits Scope Extraction**: Automatically parses Conventional Commits and isolates the scope. E.g., `feat(auth): add login` becomes `- **auth**: add login (hash)`.
- **Prepend & Inject Mode**: Intelligently inserts new release logs *directly under* the `# Changelog` main header, keeping historical logs perfectly preserved without creating redundant titles.
- **Commit Classification & Emoji Styling**: Automatically categorizes commits into clean blocks with clear visual indicators:
  - ✨ **Added**: New features (`feat`, `add`)
  - 🐛 **Fixed**: Bug fixes (`fix`, `bug`)
  - 🗑️ **Removed**: Deprecated or reverted code (`remove`, `delete`, `revert`)
  - ⚙️ **Changed & Refactored**: Refactoring, chore, docs, styles, etc.
- **Dry-run Preview Mode**: Preview generated outputs in the console without touching files.

## Usage Guide

### 🤖 Via Claude Code

Run this skill directly in your workspace prompt:
```
/generate-changelog
```

### 💻 Via Shell CLI

Alternatively, developers can invoke the script in a terminal with advanced control options:

```bash
# General run (automatically detects last git tag as start point)
./changelog.sh

# Run from a specific tag or commit hash
./changelog.sh --since v1.2.0

# Preview output in console without writing to file
./changelog.sh --dry-run

# Show interactive help docs
./changelog.sh --help
```
