# SKILL.md — Changelog Generator

## Description
Generates a structured CHANGELOG.md from git commit history, auto-categorizing commits into Added / Fixed / Changed / Removed sections. Works as a standalone bash script or can be called via `/generate-changelog` command.

## Usage

```bash
bash changelog.sh [since-tag] [output-file]

# Examples:
bash changelog.sh                      # All commits since last tag → CHANGELOG.md
bash changelog.sh v1.0.0               # Commits since v1.0.0
bash changelog.sh v1.0.0 CHANGELOG.md  # Custom output file
```

## How It Works

1. Detects last git tag (or uses provided tag)
2. Fetches commits between tag and HEAD
3. Parses conventional commits (feat:, fix:, chore:, docs:, etc.)
4. Categorizes into:
   - **Added** — feat:, feat(scope):, feat!
   - **Fixed** — fix:, fix(scope):
   - **Changed** — refactor:, style:, perf:, test:
   - **Removed** — BREAKING CHANGES, !, removed features
5. Outputs Markdown with dates, authors, and issue references

## Prerequisites

- `git`
- `awk`, `sed` (standard Unix tools)
- Optional: `gh` CLI for issue linking

## Example Output

````markdown
# Changelog

## [Unreleased]

### Added
- New user authentication module (#12)
- Rate limiting middleware for API endpoints (#15)

### Fixed
- Fix memory leak in connection pool (#14)

### Changed
- Refactor database layer for better performance (#11)

### Removed
- ~~Legacy v1 API endpoints~~ (breaking change)
````
