# Changelog Generator

Generate a structured CHANGELOG.md from git history.
Auto-categorizes commits into Added / Fixed / Changed / Removed sections.

## Setup (3 steps)

1. Copy changelog.py to your project root
2. Run: python3 changelog.py
3. Commit the generated CHANGELOG.md

## Usage

python3 changelog.py
python3 changelog.py --since v1.0.0
python3 changelog.py --output RELEASE.md

## How It Works

| Prefix | Section |
|--------|---------|
| feat: add: new: | Added |
| fix: bug: hotfix: | Fixed |
| change: refactor: perf: | Changed |
| remove: revert: drop: | Removed |

Uses Conventional Commits format.

## Requirements
- Python 3.10+
- Git