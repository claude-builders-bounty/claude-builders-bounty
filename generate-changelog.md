---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history, categorizing commits by type (Added/Fixed/Changed/Removed)
---

# Generate CHANGELOG

Automatically generates a structured `CHANGELOG.md` from your project's git history.

## Usage

```
/generate-changelog
```

This will:
1. Fetch all commits since the last git tag (or all commits if no tags exist)
2. Categorize commits by type based on conventional commit format
3. Generate a properly formatted CHANGELOG.md
4. Append to existing CHANGELOG.md or create a new one

## Commit Categorization

The skill automatically categorizes commits based on their prefix:

- **Added**: `feat:`, `feature:`, `add:`
- **Fixed**: `fix:`, `bugfix:`, `hotfix:`
- **Changed**: `change:`, `update:`, `refactor:`, `perf:`
- **Removed**: `remove:`, `delete:`
- **Other**: Commits without a recognized prefix

## Format

The generated CHANGELOG follows the [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [Unreleased] - YYYY-MM-DD

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Change description

### Removed
- Removed feature description
```

## Examples

### Basic usage
```
/generate-changelog
```

### With custom tag range
```
/generate-changelog --from v1.0.0 --to HEAD
```

### Preview without writing
```
/generate-changelog --dry-run
```

## Implementation

When invoked, this skill:

1. Runs `git describe --tags --abbrev=0` to find the last tag
2. Runs `git log <last-tag>..HEAD --pretty=format:"%h|%s|%an|%ad" --date=short`
3. Parses each commit and categorizes by prefix
4. Groups by category (Added/Fixed/Changed/Removed)
5. Formats as markdown
6. Prepends to CHANGELOG.md (or creates it)

## Notes

- Follows [Conventional Commits](https://www.conventionalcommits.org/) specification
- Preserves existing CHANGELOG.md content
- Adds new entries at the top
- Includes commit hash for reference
- Shows author and date for each entry
