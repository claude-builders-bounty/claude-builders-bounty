---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history using conventional commits
version: 1.0.0
author: Scotty Wish
command: /generate-changelog
script: changelog.sh
---

# generate-changelog

A Claude Code skill that generates a structured `CHANGELOG.md` from your project's git history. Parses conventional commit messages and groups changes into organized categories.

## Usage

In Claude Code, run:

```
/generate-changelog
```

Or directly from the terminal:

```bash
bash skills/generate-changelog/changelog.sh
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--repo PATH` | Path to git repository | `.` (current dir) |
| `--tag TAG` | Tag to start from (e.g. `v1.0.0`) | Last tag or first commit |
| `--since REF` | Git ref to start from (e.g. `HEAD~10`) | Last tag |
| `--until REF` | Git ref to end at | `HEAD` |
| `--output FILE` | Output file path | `CHANGELOG.md` |
| `--version VER` | Version string for the release | `Unreleased` |
| `--help` | Show help | |

### Examples

```bash
# Generate changelog since last tag
bash skills/generate-changelog/changelog.sh

# Generate changelog between specific tags
bash skills/generate-changelog/changelog.sh --tag v1.0.0 --until v2.0.0 --version "2.0.0"

# Generate changelog for last 5 commits
bash skills/generate-changelog/changelog.sh --since HEAD~5 --version "1.1.0"

# Specify a different repo
bash skills/generate-changelog/changelog.sh --repo /path/to/project
```

## How It Works

The skill:
1. Reads git log between two refs (or since the last tag)
2. Parses conventional commit prefixes (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `perf:`, `style:`, `ci:`, `build:`, `revert:`)
3. Groups commits into categories: **Added**, **Fixed**, **Changed**, **Removed**, **Documentation**, **Performance**, **Testing**, **Dependencies**
4. Detects breaking changes (`BREAKING CHANGE` or `!` after prefix)
5. Handles edge cases: no tags, first commit, merge commits, empty repos
6. Outputs a well-formatted `CHANGELOG.md` with version, date, and categorized entries
