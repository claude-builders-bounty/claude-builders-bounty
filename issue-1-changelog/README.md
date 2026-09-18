# Changelog Generator Skill

A Python script that acts as a tool/skill to automatically generate a structured `CHANGELOG.md` from your git history.

## Features
- Fetches all commits since the last git tag (or all commits if no tags exist).
- Auto-categorizes commit messages into: `Added`, `Fixed`, `Changed`, and `Removed`.
- Outputs a properly formatted `CHANGELOG.md` in the current directory.

## Installation & Setup

1. Copy the script to your project:
   ```bash
   cp generate-changelog.py /usr/local/bin/generate-changelog
   chmod +x /usr/local/bin/generate-changelog
   ```

2. Run it in any git repository:
   ```bash
   generate-changelog
   ```

## Sample Output
```markdown
# CHANGELOG

## Added
- feat: add new authentication module (abc1234)

## Fixed
- fix: resolve memory leak in worker (def5678)

## Changed
- update dependencies (ghi9012)
```
