# Generate Changelog Skill

Generate a structured CHANGELOG.md from git history with automatic categorization.

## Usage

```
/generate-changelog [output-file]
```

If no output file is specified, defaults to `CHANGELOG.md` in the current directory.

## What It Does

1. Fetches commits since the last git tag (or all commits if no tags exist)
2. Auto-categorizes commits into:
   - **Added** - New features, implementations
   - **Changed** - Updates, refactors, improvements
   - **Fixed** - Bug fixes, resolved issues
   - **Removed** - Deleted features, deprecations
   - **Other** - Everything else
3. Generates a properly formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format
4. Includes commit hashes with links (if remote URL is available)

## Auto-Categorization Rules

Commits are categorized based on:
- **Conventional commit prefixes**: `feat:`, `fix:`, `chore:`, etc.
- **Keywords in subject**: "Add", "Fix", "Update", "Remove", etc.
- **Case-insensitive matching** for flexibility

## Examples

```bash
# Generate CHANGELOG.md in current directory
/generate-changelog

# Generate custom named file
/generate-changelog RELEASE_NOTES.md

# Use the bash script directly
./generate-changelog.sh HISTORY.md
```

## Requirements

- Git repository
- Bash shell
- `git` command available

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-04-01

### Added
- New feature description ([abc123](url)) by @author

### Fixed
- Bug fix description ([def456](url)) by @author
```