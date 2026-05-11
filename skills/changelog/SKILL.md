---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Auto-categorizes commits into Added/Fixed/Changed/Removed sections with version grouping, commit hashes, and proper markdown formatting.
---

# /generate-changelog

Generate a structured, production-ready `CHANGELOG.md` from this project's git history.

## Usage

### Claude Code Skill

Simply say "generate changelog" or run:

```bash
python skills/changelog/changelog.py
```

### Standalone

```bash
# Since the last git tag (recommended)
python changelog.py

# Since a specific tag
python changelog.py --since v1.0.0

# Full project history (if no tags exist)
python changelog.py --full

# Custom output file
python changelog.py --output RELEASES.md

# Run against another repository
python changelog.py --repo /path/to/other/project
```

## What it does

- Fetches all commits since the last git tag (or specified since point)
- Parses **conventional commit prefixes** (`feat:`, `fix:`, `refactor:`, `perf:`)
- Falls back to **natural language** detection (`Add`, `Fix`, `Remove`, `Update`, etc.)
- Categorizes into: **✨ Added** / **🐛 Fixed** / **🔄 Changed** / **🗑️ Removed** / **🔧 Other**
- Groups commits by version tag boundaries with dates
- Includes clickable commit hash links (when a remote is configured)
- Outputs properly formatted markdown

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--since <tag>` | Latest tag | Start point for commit range |
| `--full` | — | Include full history (ignores tags) |
| `--output <file>` | `CHANGELOG.md` | Output file path |
| `--repo <path>` | `.` | Git repository path |
| `-h` / `--help` | — | Show help |

## Requirements

- Python 3.8+
- git
