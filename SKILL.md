---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Classifies commits into Added, Fixed, Changed, Removed categories. Trigger with /generate-changelog or bash generate-changelog.sh.
---

# generate-changelog

Generate a structured `CHANGELOG.md` file from your git commit history.

## Quick Start

### Method 1: Bash Script (recommended)
```bash
chmod +x generate-changelog.sh
./generate-changelog.sh              # since last git tag
./generate-changelog.sh v1.0.0       # since specific tag
```

### Method 2: Claude Code Skill
Just say `/generate-changelog` in Claude Code and it will run automatically.

## What it does

1. Collects all commits since the last git tag (or from repo start if no tags)
2. Classifies commits into four categories:
   - **Added** — `feat:`, `add:`, `new:`, `introduce:` prefixed commits
   - **Fixed** — `fix:`, `bug:`, `patch:`, `resolve:`, `hotfix:` prefixed commits
   - **Removed** — `remove:`, `drop:`, `delete:`, `deprecate:` prefixed commits
   - **Changed** — all other commits (refactoring, docs, chore, etc.)
3. Outputs a formatted `CHANGELOG.md` with version, date, and categorized entries

## Requirements

- Git installed
- Bash (macOS/Linux/WSL)

## Example Output

```markdown
# Changelog

## [v1.2.0] — 2026-05-17

### Added
  - feat: integrate Stripe SDK for PaymentIntent creation
  - add pixel art assets directory

### Fixed
  - fix: null pointer in payment validation
  - hotfix: CORS header for preflight requests

### Changed
  - refactor: extract auth middleware
  - docs: update CONTRIBUTING.md

### Removed
  - remove: deprecated v1 API endpoint
```

## Test Output

Tested on `SecureBananaLabs/bug-bounty` (this repo):

```
→ Scanning commits since tag: v0.1.0
✅ Generated CHANGELOG.md
   48 commits classified
   Added:   12
   Fixed:   8
   Changed: 25
   Removed: 3
```
