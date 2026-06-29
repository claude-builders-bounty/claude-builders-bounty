---
name: changelog-generator
version: 1.0.0
category: automation
subcategory: documentation
author: lee-muriithi-kingori
description: Generate a structured CHANGELOG.md from git history
prerequisites: [git]
license: MIT
---

# SKILL: CHANGELOG Generator

Generate a structured `CHANGELOG.md` from a project's git history. This skill automatically fetches commits since the last git tag, categorizes them, and produces a properly formatted changelog.

## Installation

```bash
git clone <your-repo-url>
cd changelog-generator
chmod +x changelog.sh
```

## Usage

### As a Claude Code Skill

```
/generate-changelog [options]
```

### As a Standalone Script

```bash
./changelog.sh [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--since` | Start date (YYYY-MM-DD) | Last tag date |
| `--to` | End date (YYYY-MM-DD) | HEAD |
| `--output` | Output file path | CHANGELOG.md |
| `--append` | Append to existing file | false |
| `--version` | Version string for header | Auto-detected |
| `--unreleased` | Mark as unreleased section | false |
| `--dry-run` | Print to stdout only | false |

## How It Works

1. **Tag Detection**: Finds the most recent git tag to determine the commit range
2. **Commit Fetching**: Retrieves all commits since the last tag (or specified date)
3. **Auto-Categorization**: Parses commit messages and categorizes into:
   - **Added** - `feat:`, `add:`, `new:` prefixes or keywords
   - **Fixed** - `fix:`, `bugfix:`, `hotfix:` prefixes or keywords
   - **Changed** - `chore:`, `update:`, `refactor:`, `perf:` prefixes
   - **Removed** - `remove:`, `delete:`, `deprecate:` prefixes
   - **Other** - Everything else (documentation, style, etc.)
4. **Formatting**: Outputs standard Keep a Changelog format

## Categories

### Added
- New features
- New functionality
- New APIs or endpoints
- New dependencies

### Fixed
- Bug fixes
- Error corrections
- Security patches

### Changed
- Performance improvements
- Refactored code
- Updated dependencies
- Configuration changes

### Removed
- Removed features
- Deprecated functionality
- Deleted files

## Example Output

```markdown
# Changelog

## [1.2.0] - 2026-06-29

### Added
- Add user authentication flow with OAuth2
- Implement dark mode toggle
- New dashboard analytics widget

### Fixed
- Fix memory leak in data processing pipeline
- Correct off-by-one error in pagination
- Resolve race condition in state management

### Changed
- Update React to version 19
- Refactor API middleware for better error handling
- Improve bundle size by 23%

### Removed
- Remove legacy jQuery dependency
- Delete deprecated `/v1/old-api` endpoint
```

## Testing

Test on your own repo:

```bash
# Clone a repo with tags
git clone https://github.com/some/project.git /tmp/test-repo
cd /tmp/test-repo

# Run the generator
../changelog.sh --dry-run

# Generate actual CHANGELOG
../changelog.sh --output CHANGELOG.md
```

## Dependencies

- `git` (>= 2.20)
- `bash` (>= 4.0)
- Standard POSIX utilities (`grep`, `sed`, `awk`, `date`)

## License

MIT - See [LICENSE](LICENSE)
