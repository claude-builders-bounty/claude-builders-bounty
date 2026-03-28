# Changelog Generator

Generate structured `CHANGELOG.md` from git history with automatic categorization.

## Installation

```bash
# Clone or download
curl -O https://raw.githubusercontent.com/yourusername/changelog-generator/main/changelog.py

# Make executable
chmod +x changelog.py
```

## Usage

### Basic Usage

```bash
# Generate changelog since last tag
python changelog.py

# Generate since specific tag
python changelog.py --since v1.0.0

# Generate from beginning of history
python changelog.py --all

# Custom output file
python changelog.py --output RELEASE_NOTES.md
```

## Features

- ✅ Auto-categorizes commits into: Added / Fixed / Changed / Removed
- ✅ Supports conventional commits (`feat:`, `fix:`, `docs:`, etc.)
- ✅ Auto-detects non-conventional commits by keywords
- ✅ Emoji prefixes for visual scanning
- ✅ BREAKING change detection
- ✅ Scope extraction for organized output
- ✅ Prepends to existing CHANGELOG.md

## Categorization Rules

| Commit Type | Category | Emoji |
|-------------|----------|-------|
| `feat`, `feature` | Added | ✨ |
| `fix`, `bugfix` | Fixed | 🐛 |
| `docs`, `doc` | Changed | 📝 |
| `style` | Changed | 💄 |
| `refactor` | Changed | ♻️ |
| `perf` | Changed | ⚡ |
| `test` | Changed | ✅ |
| `chore` | Changed | 🔧 |
| `revert` | Removed | ⏪ |
| `remove`, `delete` | Removed | 🗑️ |

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2026-03-28

### Added
- ✨ Add user authentication system
- ✨ **api**: Implement rate limiting

### Fixed
- 🐛 Fix memory leak in data processing
- 🐛 **auth**: Correct token expiration handling

### Changed
- 🔧 Update dependencies to latest versions
- ♻️ **utils**: Refactor string utilities

### Removed
- 🗑️ Drop support for Node 16
```

## Testing

Tested on this repository:

```bash
python changelog.py --all --output TEST_CHANGELOG.md
```

See `TEST_CHANGELOG.md` for sample output.

## Requirements

- Python 3.7+
- Git repository

## License

MIT
