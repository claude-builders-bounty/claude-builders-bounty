---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history"
version: 1.0.0
author: Ace-Ronin
license: MIT
---

# Generate Changelog Skill

Automatically generates a structured `CHANGELOG.md` from a project's git history, categorizing commits by type.

## Usage

```bash
/generate-changelog [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Output file path | `CHANGELOG.md` |
| `--since` | Start from this tag/commit | Last git tag |
| `--version` | Version number for this release | Auto-detected |
| `--dry-run` | Preview without writing file | `false` |

### Examples

```bash
# Generate changelog from last tag to HEAD
/generate-changelog

# Generate with custom output
/generate-changelog --output docs/CHANGELOG.md

# Preview without writing
/generate-changelog --dry-run

# Generate from specific tag
/generate-changelog --since v1.0.0
```

## Commit Type Mapping

Commits are auto-categorized based on conventional commit prefixes:

| Prefix | Category | Example |
|--------|----------|---------|
| `feat:`, `feature:`, `add:`, `new:` | **Added** | `feat: add user authentication` |
| `fix:`, `bugfix:`, `patch:`, `resolve:` | **Fixed** | `fix: resolve login timeout issue` |
| `change:`, `refactor:`, `improve:`, `update:` | **Changed** | `refactor: optimize database queries` |
| `remove:`, `delete:`, `drop:`, `deprecate:` | **Removed** | `remove: deprecated API endpoints` |
| `docs:`, `doc:`, `readme:` | **Documentation** | `docs: update API documentation` |
| `test:`, `tests:` | **Tests** | `test: add unit tests for auth` |
| `chore:`, `ci:`, `build:` | **Chore** | `chore: update dependencies` |
| Other | **Other** | Any uncategorized commit |

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New feature description

### Fixed
- Bug fix description

---

## [v1.2.0] - 2026-05-07

### Added
- feat: add user authentication system
- feat: implement password reset flow

### Fixed
- fix: resolve login timeout issue
- fix: correct date formatting in reports

### Changed
- refactor: optimize database queries
- update: upgrade to Next.js 15

### Removed
- remove: deprecated API v1 endpoints
```

## Implementation

The skill uses `git log` to fetch commits and categorizes them using conventional commit patterns.

### Git Commands Used

```bash
# Get commits since last tag
git log --pretty=format:"%h|%s|%an|%ad" --date=short $(git describe --tags --abbrev=0 2>/dev/null || echo "")..HEAD

# Get all tags
git tag --sort=-version:refname

# Get last tag
git describe --tags --abbrev=0 2>/dev/null
```

## Requirements

- Git installed and configured
- Repository with git history
- Conventional commits format recommended (but not required)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No tags found | Uses initial commit as baseline |
| Empty changelog | No commits since last tag |
| Wrong categorization | Use conventional commit prefixes |

## License

MIT
