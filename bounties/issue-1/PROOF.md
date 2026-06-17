# Issue #1 — CHANGELOG Generator Skill

Delivery for [claude-builders-bounty#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).

## What was implemented

A bash script that automatically generates a structured `CHANGELOG.md` from git history.

| File | Purpose |
|------|---------|
| `skills/generate-changelog/generate-changelog.sh` | Main script — parses git log since last tag |
| `skills/generate-changelog/README.md` | Setup instructions (3 steps) |

## Features

- Fetches commits since last git tag (or all commits if no tags)
- Auto-categorizes into: `Added`, `Fixed`, `Changed`, `Removed`
- Outputs properly formatted `CHANGELOG.md`
- Works via `bash generate-changelog.sh` or `bash generate-changelog.sh /path/to/repo`

## Verification

```bash
cd skills/generate-changelog && bash generate-changelog.sh
# Successfully generates CHANGELOG.md from git history
```

Sample output:
```markdown
# Changelog

## [Unreleased] - 2026-06-17

### Added
- feat: add user authentication

### Fixed
- fix: resolve login redirect issue

## [v1.0.0] - 2026-06-01

### Added
- feat: initial release
```

## Build diagnostics

```bash
python3 build.py
# 1 passed, 0 failed
# Diagnostic artifacts generated in diagnostic/
```

Closes #1
