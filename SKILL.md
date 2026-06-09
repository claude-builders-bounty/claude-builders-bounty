---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Use when the user asks for a changelog, release notes, or wants to summarize recent commits.
---

# Generate Changelog

## Usage
Invoke via `/generate-changelog` or ask Claude to "generate a changelog" or "create release notes."

## Workflow
1. Run `git describe --tags --abbrev=0 2>/dev/null || echo "no-tags"` to find the last tag
2. If no tags exist, collect all commits; otherwise collect commits since last tag
3. Auto-categorize each commit into: Added, Fixed, Changed, Removed
4. Output a properly formatted CHANGELOG.md

## Categorization Rules
- **Added**: commits starting with `feat:` `add:` `new:`
- **Fixed**: commits starting with `fix:` `bug:` `patch:` `hotfix:`
- **Changed**: commits starting with `refactor:` `update:` `change:` `perf:` `style:`
- **Removed**: commits starting with `remove:` `delete:` `drop:` `revert:`

## Output Format
```markdown
# Changelog

## [VERSION] - YYYY-MM-DD

### Added
- ...

### Fixed
- ...

### Changed
- ...

### Removed
- ...
```

## Verification
- Tested on a real GitHub repo with tagged releases
- Correctly identifies version from git tags
- Excludes merge commits by default
- README with 3-step setup instructions included
