---
name: generate-changelog
description: Automatically generate a structured CHANGELOG.md from git history, categorized by Added/Fixed/Changed/Removed
version: 1.0.0
author: hermes
metadata:
  hermes:
    tags: [changelog, git, release-notes, automation]
    command: /generate-changelog
---

# Generate CHANGELOG

Automatically generates a structured `CHANGELOG.md` from a project's git history, organized by conventional commit types.

## Usage

```bash
/generate-changelog        # Generate CHANGELOG.md from last tag
```

Or run directly:
```bash
python3 changelog.py       # Generate in current directory
python3 changelog.py /path/to/repo  # Generate in specified repo
```

## Output Example

```markdown
# Changelog

## [1.2.0] - 2026-05-15

### Added
- New dark mode support
- User authentication via OAuth2

### Fixed
- Memory leak in websocket handler
- Login crash on iOS 18

### Changed
- Upgrade dependencies to latest versions
- Optimize database queries

### Removed
- Deprecated v1 API endpoints
```

## How it works

1. Finds the latest git tag (falls back to `HEAD` if no tags)
2. Fetches all commit messages since that tag
3. Parses conventional commit prefixes (`feat:`, `fix:`, `BREAKING:`, etc.)
4. Categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
5. Writes `CHANGELOG.md` in standard keepachangelog format
