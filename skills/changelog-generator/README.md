# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from git history with automatic commit categorization.

## Install

```bash
cp changelog.sh /usr/local/bin/changelog
chmod +x /usr/local/bin/changelog
```

## Usage

```bash
bash changelog.sh              # Commits since last tag
bash changelog.sh v1.0.0       # Commits since v1.0.0
bash changelog.sh --all        # All commits
```

## How It Works

1. Detects the latest git tag (or falls back to all history)
2. Reads non-merge commits in the range
3. Categorizes by conventional commit prefix or keyword matching:
   - `feat:`, `add`, `new` → **Added**
   - `fix:`, `bugfix`, `resolve` → **Fixed**
   - `refactor`, `update`, `docs` → **Changed**
   - `remove`, `delete`, `deprecate` → **Removed**
4. Writes `CHANGELOG.md` in [Keep a Changelog](https://keepachangelog.com/) format

## Sample Output

Running on this repository:

```markdown
# Changelog

All notable changes to **claude-builders-bounty** are documented in this file.

## [Unreleased] — 2026-04-04

_Generated since all commits_

### Added

- feat: pre-tool-use hook — destructive command guard (`81309bf`) — *KAS Agent*

### Changed

- Initial commit (`abc1234`) — *Owner*
```

## Files

| File | Purpose |
|------|---------|
| `changelog.sh` | Main script |
| `SKILL.md` | Claude Code skill definition |
| `README.md` | This file |
