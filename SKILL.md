# /generate-changelog

Generate a structured CHANGELOG.md from a project's git history.

## When to use

Use this skill when the user wants to create or update a changelog based on recent git commits, especially before a release or when preparing a PR.

## What it does

- Fetches commits since the last git tag (or all commits if no tag exists)
- Skips merge commits
- Parses conventional commit prefixes (feat, fix, chore, refactor, etc.)
- Auto-categorizes entries into:
  - **Added**
  - **Fixed**
  - **Changed**
  - **Removed**
- Outputs a properly formatted `CHANGELOG.md`

## Usage

```bash
bash generate-changelog.sh
```

Optional arguments:

```bash
bash generate-changelog.sh --since-tag v1.0.0 --output RELEASE_NOTES.md
bash generate-changelog.sh --since 2024-01-01 --until HEAD
```

## Requirements

- A git repository
- Bash shell (Linux, macOS, or Windows with Git Bash/WSL)

## Output example

```markdown
# Changelog

## Changes since v1.0.0

### Added
- new dashboard widget

### Fixed
- login timeout issue

### Changed
- improve caching performance
```
