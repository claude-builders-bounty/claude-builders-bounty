# CHANGELOG Generator Skill

## Overview

A Claude Code skill that automatically generates structured `CHANGELOG.md` files from git history. Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.

## Commands

```bash
# Via skill command
/generate-changelog

# Via bash wrapper
bash changelog.sh

# Via Python script directly
python3 generate_changelog.py --repo /path/to/repo --output CHANGELOG.md
```

## Setup (3 steps or fewer)

1. Copy `generate_changelog.py` and `changelog.sh` into your project root
2. `chmod +x changelog.sh`
3. Run `./changelog.sh`

## Options

| Flag | Description |
|------|-------------|
| `--repo PATH` | Path to target git repo (default: current directory) |
| `--output FILE` | Output file path (default: CHANGELOG.md) |
| `--since-tag TAG` | Only show commits after this tag |
| `--version STRING` | Version header (default: Unreleased) |

## Example

```bash
python3 generate_changelog.py --repo . --since-tag v1.0.0 --output CHANGELOG.md --version "1.1.0"
```

## Categories

Commits are auto-categorized based on message keywords:

- **Added**: `add`, `create`, `feat`, `new`, `implement`, `introduce`
- **Fixed**: `fix`, `bug`, `repair`, `resolve`, `patch`, `correct`
- **Changed**: `update`, `modify`, `change`, `refactor`, `improve`, `enhance`, `optimize`
- **Removed**: `remove`, `delete`, `deprecate`, `drop`

## Output Format

Follows [Keep a Changelog](https://keepachangelog.com/) standard with SemVer.
