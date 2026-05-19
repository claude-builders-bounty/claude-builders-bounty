# Generate CHANGELOG from Git History

## Description
A Claude Code skill that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

Invoke this skill with:
```
/generate-changelog
```

Or specify a version:
```
/generate-changelog v1.2.0
```

## What it does

1. Fetches all commits since the last git tag (or from the beginning if no tags exist)
2. Auto-categorizes commits into:
   - **Added**: New features
   - **Fixed**: Bug fixes
   - **Changed**: Changes to existing functionality
   - **Removed**: Removed features
   - **Security**: Security-related changes
3. Generates a properly formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format

## Categorization Logic

The skill analyzes commit messages for keywords:

| Category | Keywords |
|----------|----------|
| Added | `add`, `new`, `create`, `implement`, `introduce`, `feature` |
| Fixed | `fix`, `bug`, `patch`, `resolve`, `correct`, `repair` |
| Changed | `change`, `update`, `modify`, `refactor`, `improve`, `enhance` |
| Removed | `remove`, `delete`, `drop`, `deprecate` |
| Security | `security`, `vulnerability`, `cve`, `xss`, `injection` |

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New user authentication system
- Dark mode support

### Fixed
- Login button not responding on mobile
- Memory leak in image processing

### Changed
- Improved API response times by 40%
- Updated dependencies to latest versions

### Security
- Patched XSS vulnerability in comment form

## [1.0.0] - 2024-01-15

### Added
- Initial release
```

## Implementation

When this skill is invoked, Claude will:

1. Run `git tag --sort=-v:refname` to get the latest tag
2. Run `git log --pretty=format:"%s"` to get commit messages
3. Parse and categorize each commit
4. Generate the CHANGELOG.md content
5. Write to `CHANGELOG.md` in the project root

## Notes

- Commits are grouped by their semantic meaning
- Breaking changes are highlighted
- Dates are automatically extracted from tags
- Supports conventional commits format (`feat:`, `fix:`, etc.)

## Dependencies

- Git CLI installed and available in PATH
- Repository must have git history

---

*Bounty #1 Implementation by @gacorpoll-ui*
