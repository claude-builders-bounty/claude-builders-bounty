---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Fetches commits since last tag, categorizes into Added/Fixed/Changed/Removed, outputs formatted markdown. Usage: /generate-changelog or bash changelog.sh
---

# Generate Changelog Skill

## Usage
- Command: `/generate-changelog`
- Script: `bash changelog.sh`

## Implementation
The script parses `git log` since the last tag (or all commits if no tags), categorizes by conventional commit prefixes, and writes CHANGELOG.md.

### Categories
- feat -> Added
- fix -> Fixed
- refactor, perf, style -> Changed
- revert, remove, delete -> Removed
- docs, test, ci, chore, build -> skipped (not user-facing)

### Output Format
```markdown
# Changelog

## [Unreleased]
### Added
- description (commit-hash)

### Fixed
- description (commit-hash)

### Changed
- description (commit-hash)

### Removed
- description (commit-hash)
```
