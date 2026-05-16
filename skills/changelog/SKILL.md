---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# Generate Changelog

Generate a structured CHANGELOG.md from the project's git history.

## Usage

Run `/generate-changelog` or execute `bash skills/changelog/changelog.sh` directly.

## How it works

1. Finds the last git tag (or first commit if no tags)
2. Extracts commits since that tag
3. Categorizes by Conventional Commits prefix:
   - `feat:` → Added
   - `fix:` → Fixed
   - `refactor:`, `perf:`, `chore:` → Changed
   - `remove:`, `delete:` → Removed
4. Outputs formatted CHANGELOG.md

## Output format

```markdown
## [version] — YYYY-MM-DD

### Added
- feature description (commit-hash)

### Fixed
- bug fix description (commit-hash)

### Changed
- refactor description (commit-hash)

### Removed
- removal description (commit-hash)
```
