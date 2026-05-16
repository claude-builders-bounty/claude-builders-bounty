# changelog.sh — Generate Structured CHANGELOG from Git History

Automatically generates a `CHANGELOG.md` file from your git commit history using Conventional Commits format.

## Quick Start

```bash
# Generate changelog from last tag to HEAD
bash changelog.sh

# Specify custom repo and output
bash changelog.sh --repo /path/to/repo --output CHANGES.md

# Generate from specific tag
bash changelog.sh --since v1.0.0
```

## Features

- ✅ Fetches commits since last git tag (or all commits if no tags)
- ✅ Auto-categorizes into: Added / Fixed / Changed / Removed / Security / Deprecated / Documentation
- ✅ Supports Conventional Commits format (`feat:`, `fix:`, `docs:`, etc.)
- ✅ Fallback keyword detection for non-conventional commits
- ✅ Outputs properly formatted CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- ✅ Filters out merge commits
- ✅ Includes preview of generated changelog

## Usage

```bash
bash changelog.sh [OPTIONS]

OPTIONS:
  --repo PATH      Path to git repository (default: current directory)
  --output FILE    Output file name (default: CHANGELOG.md)
  --since TAG      Generate changelog since specific tag (default: last tag)
```

## Examples

### Basic Usage
```bash
bash changelog.sh
```

### Custom Output Location
```bash
bash changelog.sh --output docs/CHANGELOG.md
```

### Generate from Specific Tag
```bash
bash changelog.sh --since v2.0.0
```

### Different Repository
```bash
bash changelog.sh --repo ~/projects/myapp --output ~/Desktop/CHANGELOG.md
```

## Commit Format Support

### Conventional Commits (Recommended)
```
feat: add user authentication
fix: resolve memory leak in parser
docs: update API documentation
refactor: simplify database queries
perf: optimize image loading
remove: delete deprecated endpoints
security: patch XSS vulnerability
deprecate: mark old API as deprecated
```

### Keyword Detection (Fallback)
If commits don't follow Conventional Commits, the script detects keywords:
- **Added**: "add", "new", "implement"
- **Fixed**: "fix", "bug", "resolve"
- **Changed**: "update", "change", "modify"
- **Removed**: "remove", "delete"

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-05-16

### Added
- User authentication system
- API rate limiting

### Fixed
- Memory leak in parser
- Database connection timeout

### Changed
- Simplified database queries
- Updated dependencies

### Security
- Patched XSS vulnerability
```

## Requirements

- Bash 4.0+
- Git 2.0+

## Testing

Tested on:
- ✅ Linux (Ubuntu 22.04, Debian 12)
- ✅ macOS (Ventura, Sonoma)
- ✅ WSL2 (Ubuntu)

## License

MIT
