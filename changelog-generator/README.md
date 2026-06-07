# Changelog Generator

Generate a structured `CHANGELOG.md` from git history, auto-categorizing
commits using Conventional Commits prefixes.

## Setup

```bash
chmod +x changelog-generator/changelog.sh
```

## Usage

As a Claude Code skill:
```
/generate-changelog
```

Or directly:
```bash
bash changelog-generator/changelog.sh --output CHANGELOG.md
```

## Features

- Finds commits since the latest git tag
- Categorizes into: **Added**, **Fixed**, **Changed**, **Removed**
- Skips merge commits
- Conventional Commits-aware: `feat:` -> Added, `fix:` -> Fixed, etc.
- Works on repos with no tags (marks as "Unreleased")

### Example Output

```markdown
## v1.2.0 -> HEAD

### Added
- feat: add user authentication module
- add: implement dark mode toggle

### Fixed
- fix: resolve login redirect loop
- hotfix: patch XSS vulnerability in comments

### Changed
- refactor: extract shared form validation
- deps: update lodash to 4.17.21

### Removed
- remove: drop legacy IE11 polyfills
```
