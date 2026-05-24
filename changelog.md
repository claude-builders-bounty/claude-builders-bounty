# Auto Changelog Generator

Generates a structured CHANGELOG.md from git history.

## Setup (3 steps)

1. Download the script:


2. Make it executable:


3. Run it in any git repository:


## What It Does

- Fetches commits since the last git tag (or last 50 if no tags)
- Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
- Outputs a properly formatted 
- Includes commit hashes, authors, and dates

## Categories

| Category | Keywords |
|----------|----------|
| Added | feat, add, new, introduce, implement, create, support |
| Fixed | fix, bug, repair, resolve, patch, correct, hotfix |
| Changed | change, update, refactor, rework, modify, improve, enhance, optimize |
| Removed | remove, delete, drop, deprecate, clean, purge |
