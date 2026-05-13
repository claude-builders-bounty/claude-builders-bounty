---
name: changelog-generator
description: >
  Generate structured CHANGELOG.md from git history. Auto-categorizes commits
  into Added / Fixed / Changed / Removed / Security sections based on
  conventional commit prefixes.
compatibility:
  requires: [git, bash]
---

# Changelog Generator

> Claude Code Skill for automated changelog generation

## Overview

This skill generates a structured, Keep a Changelog-compliant `CHANGELOG.md` from git
history. It fetches commits since the last git tag, categorizes them using conventional
commit prefixes, and outputs a clean Markdown changelog.

## Usage

```
/changelog-generator          → Generate full changelog since last tag
/changelog-generator --all    → Include all commits (no tag filtering)
/changelog-generator v1.0.0   → Generate changelog since specific tag
/changelog-generator --dry-run → Preview without writing file
```

## Categorization Rules

| Commit Prefix | Category |
|---------------|----------|
| `feat:` `feat(...)` `add:` `added:` | **Added** |
| `fix:` `fix(...)` `bug:` `hotfix:` | **Fixed** |
| `refactor:` `perf:` `style:` `chore:` `deps:` `ci:` `build:` | **Changed** |
| `remove:` `revert:` `drop:` | **Removed** |
| `security:` `vuln:` | **Security** |
| everything else | **Changed** |

## Output Format

Follows [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [Unreleased]

### Added
- feat: Add user authentication with OAuth2 support
- feat: Implement dark mode toggle

### Fixed
- fix: Resolve race condition in websocket handler (#42)
- fix: Correct date formatting in report export

### Changed
- refactor: Migrate from Express to Fastify
- deps: Bump typescript from 5.3 to 5.5

### Removed
- remove: Drop legacy XML API endpoint
```

## Integration

This skill can be used:
1. **Interactively** via `/changelog-generator`
2. **In CI/CD** via `bash changelog.sh`
3. **As a git hook** (post-release): `cp changelog.sh .git/hooks/post-release`

## Example

```bash
$ bash changelog.sh
✅ Found 23 commits since v2.1.0
📝 Generated CHANGELOG.md with 5 categories
   Added: 3 entries
   Fixed: 2 entries
   Changed: 15 entries
   Removed: 1 entry
   Security: 2 entries
```
