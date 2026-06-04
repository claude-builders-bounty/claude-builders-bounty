---
name: git-changelog
description: "Generate structured CHANGELOG from git history using conventional commit parsing. Auto-detects versions, groups by type, outputs Markdown."
version: 1.0.0
tags: [git, changelog, release, documentation]
---

# Git Changelog Generator

Automatically generates structured CHANGELOG.md from git history.

## Usage

```
/skill git-changelog
```

Or specify a range:

```
/skill git-changelog --from v1.0.0 --to HEAD
```

## What it does

1. Parses `git log` using conventional commit format (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `perf:`, `test:`, `ci:`)
2. Groups commits by type
3. Extracts version tags for section headers
4. Outputs a clean Markdown CHANGELOG.md

## Output Format

```markdown
# Changelog

## [v1.2.0] - 2026-06-04

### Added
- feat: add user authentication
- feat: implement dark mode

### Fixed
- fix: resolve login timeout issue
- fix: correct navbar alignment on mobile

### Changed
- refactor: simplify API client
- chore: update dependencies

## [v1.1.0] - 2026-05-28

...
```

## Implementation

The skill executes `git log --oneline --decorate` between version tags, parses conventional commit prefixes, groups results, and writes CHANGELOG.md.
