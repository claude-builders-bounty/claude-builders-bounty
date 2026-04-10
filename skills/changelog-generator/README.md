# Changelog Generator — Claude Code Skill

Generate a structured CHANGELOG.md from git history using conventional commits.

## Install (2 commands)

```bash
cp generate-changelog ~/.claude/skills/generate-changelog
chmod +x ~/.claude/skills/generate-changelog
```

## Usage

```
/changelog           # Full history
/changelog 2026-01-01  # Since specific date
```

## Output Format

Groups commits by date, then categorizes by type:
- **Breaking Changes** — `BREAKING` or `!:` prefixed
- **Added** — `feat:` commits
- **Fixed** — `fix:` commits  
- **Changed** — `refactor:` commits
- **Performance** — `perf:` commits
- **Documentation** — `docs:` commits
- **Tests** — `test:` commits
- **Build** — `ci:` / `build:` commits

## Features

- Pure bash, zero dependencies
- Follows [Keep a Changelog](https://keepachangelog.com/) format
- Supports conventional commits classification
- Groups by date (descending) and category
- Shows commit hash and author
- Works with any git repository

## Requirements

- Bash 4+ (associative arrays)
- Git repository
