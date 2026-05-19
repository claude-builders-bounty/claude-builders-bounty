# Auto-Changelog Generator

A simple bash script to automatically generate a structured `CHANGELOG.md` based on Git history since the last tag.

## Features
- Fetches all commits since the last Git tag (or all commits if no tags exist).
- Auto-categorizes commits based on conventional prefixes (`feat`, `fix`, `add`, `update`, `remove`, etc.) into `Added`, `Fixed`, `Changed`, `Removed`, and `Other`.
- Generates a beautifully formatted Markdown `CHANGELOG.md`.

## Setup and Usage
1. Make the script executable: `chmod +x changelog.sh`
2. Run it inside any Git repository: `./changelog.sh`
3. View the results: `cat CHANGELOG.md`

## Sample Output
```md
# CHANGELOG

## Changes since v1.0.0

### Added
- feat: add new login page
- add: support for new api endpoints

### Fixed
- fix: resolve race condition in database

### Changed
- refactor: clean up messy authentication logic
- chore: update dependencies
```
