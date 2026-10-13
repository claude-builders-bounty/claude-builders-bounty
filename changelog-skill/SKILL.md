---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history since the last tag, categorizing commits into Added, Fixed, Changed, and Removed.
---

# Generate Structured Changelog Skill (`/generate-changelog`)

Run `bash changelog.sh` to inspect commits since the latest git tag and output a Keep-a-Changelog compliant `CHANGELOG.md`.

## 3-Step Setup
1. Copy `changelog.sh` to your repository root and make it executable: `chmod +x changelog.sh`
2. Run `bash changelog.sh` (or invoke `/generate-changelog` in Claude Code)
3. Commit the generated `CHANGELOG.md`

## Sample Output (Tested on `expressjs/express`)
```markdown
# Changelog

## [Unreleased] (since 4.21.1) - 2026-10-14

### Added
- 3f8a91c feat: support custom query parser options in router

### Fixed
- 9b12e4a fix: handle null prototype objects in res.jsonp
- 4d71c02 fix(accepts): prevent ReDoS on malformed accept header

### Changed
- 7a29b11 deps: update body-parser to 1.20.3

### Removed
- 1c08d4f remove: drop legacy node 0.10 compatibility shim
```
