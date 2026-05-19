# Git Changelog Generator

Generate a structured `CHANGELOG.md` from git history.

The script finds commits since the latest git tag, categorizes them into `Added`, `Fixed`, `Changed`, and `Removed`, then writes a Markdown changelog.

## Setup in 3 steps

```bash
cp changelog.py /path/to/your/repo/
cd /path/to/your/repo
python3 changelog.py
```

Optional:

```bash
python3 changelog.py --since-tag v1.0.0 --output CHANGELOG.md
```

## How categories work

The script understands conventional commit prefixes:

- `feat:` -> `Added`
- `fix:` -> `Fixed`
- `refactor:`, `docs:`, `test:`, `ci:`, `chore:` -> `Changed`
- `remove:` / `revert:` -> `Removed`

For non-conventional commits, it falls back to keyword matching.

## Sample output

```md
# Changelog

All notable changes are generated from git commit history.

## Unreleased - 2026-05-18

_Changes since v1.0.0._

### Added

- Add user profile page (a1b2c3d)

### Fixed

- Correct API timeout handling (d4e5f6a)
```
