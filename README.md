# Changelog Generator

A simple bash script to automatically generate a structured `CHANGELOG.md` from your git history since the last tag.

## Setup (3 steps)
1. Copy `changelog.sh` to your project root.
2. Run `chmod +x changelog.sh`.
3. Execute `./changelog.sh`.

## How it Works
- It finds the latest git tag using `git describe`.
- It fetches all commits since that tag.
- It auto-categorizes commits based on keywords (`feat`, `fix`, `refactor`, `remove`).
- It outputs a Markdown formatted `CHANGELOG.md`.

## Sample Output
```markdown
## [2026-06-11] 
### Added
- feat: add first feature
### Fixed
- fix: resolve critical bug
### Changed
- refactor: improve performance
### Removed
- remove: delete obsolete module
```
