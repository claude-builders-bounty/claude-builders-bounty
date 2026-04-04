# Changelog Generator

Generate a structured CHANGELOG.md from your project's git history automatically.

## What it does

Parses git commits since the last tag and categorizes them into **Added**, **Fixed**, **Changed**, and **Removed** sections following [Keep a Changelog](https://keepachangelog.com) conventions.

## How to use

### Option 1: Bash script

```bash
# From your project root:
./changelog.sh

# Since a specific tag:
./changelog.sh --since v1.2.0

# Custom output file:
./changelog.sh --output docs/CHANGELOG.md
```

### Option 2: Claude Code command

Ask Claude Code:
> Generate a changelog from my git history since the last tag

Claude will run `changelog.sh` and produce a formatted CHANGELOG.md.

## Setup (3 steps)

1. Copy `changelog.sh` to your project root
2. `chmod +x changelog.sh`
3. Run `./changelog.sh`

## How categorization works

Commits are categorized by their prefix/keywords:

| Category | Triggers |
|----------|----------|
| **Added** | `add`, `feat`, `new`, `create`, `implement`, `introduce`, `support` |
| **Fixed** | `fix`, `bug`, `patch`, `resolve`, `repair`, `correct`, `hotfix` |
| **Changed** | `change`, `update`, `refactor`, `improve`, `optimize`, `rename`, `move`, `migrate`, `bump` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate`, `strip`, `cleanup` |

Commits that don't match any prefix are checked for keywords anywhere in the message. Remaining commits go to **Other**.

## Requirements

- Git repository with commits
- Bash 4+
- Optional: git tags for version-based changelogs
