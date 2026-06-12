---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history"
version: 1.0.0
---

# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from git history.

## Usage

```bash
bash generate-changelog.sh [output-file]
```

Or as a Claude Code skill: `/generate-changelog`

## What It Does

1. Detects the last git tag and scans commits since that tag
2. Categorizes commits using conventional commit prefixes:
   - **Added**: `feat`, `add`, `new`, `implement`, `introduce`, `create`
   - **Fixed**: `fix`, `bug`, `resolve`, `patch`, `hotfix`, `correct`
   - **Removed**: `remove`, `drop`, `delete`, `deprecate`, `retire`
   - **Changed**: everything else
3. Outputs a formatted `CHANGELOG.md`

## Installation

1. Copy `generate-changelog.sh` to your project root
2. Make executable: `chmod +x generate-changelog.sh`
3. Run: `bash generate-changelog.sh`

## Example

```markdown
# Changelog

## [v1.2.0] — 2026-06-12

### Added
- feat: add dark mode toggle

### Fixed
- fix: login redirect loop

### Changed
- docs: update API reference

### Removed
- remove: deprecated v1 endpoint
```
