# Generate Changelog

A bash script that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Features

- 📊 Auto-categorizes commits: Added / Fixed / Changed / Removed / Docs / Tests / Security
- 🔗 Links PR numbers to GitHub PR pages
- 🏷️ Works with or without git tags
- 📅 Includes date in version header
- 🎨 Follows Keep a Changelog format

## Installation

```bash
# Clone or download
curl -O https://raw.githubusercontent.com/yourusername/generate-changelog/main/generate-changelog.sh
chmod +x generate-changelog.sh

# Optional: Add to PATH
sudo mv generate-changelog.sh /usr/local/bin/generate-changelog
```

## Usage

### Basic
```bash
./generate-changelog.sh
```

### Custom output file
```bash
./generate-changelog.sh RELEASE_NOTES.md
```

### With Claude Code
```
/generate-changelog
```

## How It Works

1. Detects commits since the last git tag (or all commits if no tags)
2. Categorizes based on commit message prefixes:
   - `feat:` → 🚀 Added
   - `fix:` → 🐛 Fixed
   - `refactor:`/`update:` → 🔧 Changed
   - `remove:` → 🗑️ Removed
   - `docs:` → 📚 Documentation
   - `test:` → 🧪 Tests
   - `security:` → 🔒 Security
3. Extracts PR numbers (#123) and creates links
4. Outputs formatted Markdown

## Example Output

```markdown
# Changelog

## [2024-03-29]

### 🚀 Added
- New user authentication system [#45](https://github.com/user/repo/pull/45)
- Dark mode support [#42](https://github.com/user/repo/pull/42)

### 🐛 Fixed
- Login timeout issue [#44](https://github.com/user/repo/pull/44)
```

## Requirements

- Bash 4.0+
- Git

## License

MIT
