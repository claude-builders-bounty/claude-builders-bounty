---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history with conventional commits parsing
version: 1.0.0
author: shuibui
tags: [changelog, git, conventional-commits, automation]
---

# Generate CHANGELOG Skill

Automatically generates a structured `CHANGELOG.md` from your project's git history, supporting [Conventional Commits](https://www.conventionalcommits.org/).

## Usage

```bash
bash skills/generate-changelog/changelog.sh
# or
python3 skills/generate-changelog/generate_changelog.py
```

## Flags

| Flag | Description |
|------|-------------|
| `--output FILE` | Output file (default: CHANGELOG.md) |
| `--since TAG` | Start from tag (default: last git tag) |
| `--dry-run` | Print to stdout only |
| `--include-merges` | Include merge commits |
| `--format text|json` | Output format |

## Categorization

- `feat:` → **Added**
- `fix:` → **Fixed**
- `docs:` → **Documentation**
- `style:` → **Styling**
- `refactor:` → **Changed**
- `perf:` → **Performance**
- `test:` → **Tests**
- `build:` → **Build**
- `ci:` → **CI**
- `chore:` → **Chores**

## Requirements

- `git` available in PATH
- Python 3.6+ (for Python version)
