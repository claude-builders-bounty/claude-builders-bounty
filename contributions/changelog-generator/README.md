# 📋 changelog.sh — Structured CHANGELOG Generator

> **Bounty**: [#1 $50](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

Automatically generates a formatted `CHANGELOG.md` from git history.

## Quick Start (3 steps)

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/claude-builders-bounty/main/contributions/changelog-generator/changelog.sh

# 2. Run
bash changelog.sh

# 3. Check
cat CHANGELOG.md
```

## Features

- ✅ Auto-categorizes: `Added` / `Fixed` / `Changed` / `Removed`
- ✅ Auto-detects latest tag (or use `--tag v1.0.0`)
- ✅ Standard conventional commit prefixes + Chinese keywords
- ✅ No dependencies — pure bash

## Options

| Option | Description |
|--------|-------------|
| `--tag v1.0.0` | Compare against a specific tag |
| `--output CHANGELOG.md` | Custom output path |
| `--repo /path` | Target repository |

## Sample Output

```
# Changelog

## [v0.1.0] - 2026-05-17

### ✨ Added
- feat: add user authentication module

### 🐛 Fixed
- fix: resolve edge case in parser
```
