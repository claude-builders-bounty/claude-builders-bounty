---
name: generate-changelog
description: Generate structured CHANGELOG.md from git history using conventional commit parsing
---

# Generate CHANGELOG

## Description
Automatically generates a structured `CHANGELOG.md` from a project's git history.
Categorizes commits into: Added / Fixed / Changed / Removed based on conventional commit prefixes.

## Usage
Run via Claude Code: `/generate-changelog`
Or standalone: `bash changelog.sh`

## How it works
1. Finds the last git tag (or the initial commit if no tags exist)
2. Parses all commits since that tag
3. Categorizes by conventional commit prefix:
   - `feat:` / `add:` → **Added**
   - `fix:` / `bug:` → **Fixed**
   - `refactor:` / `update:` / `chore:` → **Changed**
   - `remove:` / `rm:` / `delete:` → **Removed**
4. Outputs a clean, properly formatted CHANGELOG.md

## Requirements
- bash
- git (with commit history)

## Example output
```markdown
# Changelog

Generated from `v1.0.0` to `HEAD`

## Added
- feat: add user authentication
- feat: implement rate limiting

## Fixed
- fix: resolve timeout issue in API calls
- bug: correct pagination offset

## Changed
- refactor: optimize database queries
- chore: update dependencies

## Removed
- remove: deprecated endpoint
```
