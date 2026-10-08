# Changelog Generator

Automatically generate a structured `CHANGELOG.md` from your git history.

## Setup

1. **Clone or download** this repository
2. **Navigate** to your project directory (must be a git repository)
3. **Run** the script:
   ```bash
   bash /path/to/changelog.sh
   ```

## Features

- 📋 Fetches commits since the last git tag
- 🏷️ Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- 📝 Outputs a properly formatted `CHANGELOG.md`
- 🎯 Supports conventional commit prefixes (feat:, fix:, etc.)

## Categories

Commits are categorized based on:
- **Added**: New features, additions (feat:, add:, new:)
- **Fixed**: Bug fixes (fix:, bugfix:, hotfix:)
- **Changed**: Updates, improvements (change:, update:, refactor:)
- **Removed**: Deletions, deprecations (remove:, delete:, drop:)

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.0.0] - 2025-05-22

### Added
- New user authentication system (a1b2c3d)
- Dark mode support (e4f5g6h)

### Fixed
- Login page redirect bug (i7j8k9l)
```

## Requirements

- Python 3.x or Python 2.7
- Git repository with commit history

## License

MIT
