# Git Changelog Generator

Generate structured, categorized changelogs from your git history.

## Quick Start

```bash
# Generate from current directory
./generate-changelog

# Output to file
./generate-changelog --output CHANGELOG.md

# From a specific tag/version
./generate-changelog --from v1.0.0

# Compact format
./generate-changelog --format compact

# From a different repo
./generate-changelog --repo /path/to/project
```

## Features

- Parses conventional commits (`feat:`, `fix:`, `docs:`, etc.)
- Groups changes by type with emoji headers
- Full and compact output formats
- Works with any git repository
- Optional tag-based version ranges
- Zero dependencies (pure Python + git)

## Example Output

```
# Changelog
*Generated on 2025-06-15*
Total commits: 42

## 🚀 Features
- Add user authentication with OAuth
  - Commit: `abc123` | Date: 2025-06-10

## 🐛 Bug Fixes
- Fix pagination in search results
  - Commit: `def456` | Date: 2025-06-09

## 📚 Documentation
- Update API reference
  - Commit: `ghi789` | Date: 2025-06-08
...
```

## Requirements

- Python 3.8+
- Git 2.0+
- No external Python packages needed
