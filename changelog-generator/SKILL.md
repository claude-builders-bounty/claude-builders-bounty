# Changelog Generator Skill

## Description
Generate a structured CHANGELOG.md from git history, auto-categorizing commits into Added/Fixed/Changed/Removed sections.

## Usage
```
/generate-changelog
```

## How it works
1. Detects the last git tag (or uses first commit if no tags exist)
2. Fetches all commits since that tag
3. Categorizes commits by conventional commit prefixes:
   - `feat:` / `add:` → **Added**
   - `fix:` / `bugfix:` → **Fixed**
   - `refactor:` / `change:` / `update:` → **Changed**
   - `remove:` / `delete:` / `deprecate:` → **Removed**
4. Outputs a formatted `CHANGELOG.md`

## Setup (3 steps)
1. Clone this skill into your project
2. Run `bash changelog.sh` or `python3 generate_changelog.py`
3. Check the generated `CHANGELOG.md`

## Commands
- `bash changelog.sh` — Bash version (zero dependencies)
- `python3 generate_changelog.py` — Python version (more robust parsing)
