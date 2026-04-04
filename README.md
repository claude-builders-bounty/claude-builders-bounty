# Changelog Generator

Automatically generate a structured `CHANGELOG.md` from your git commit history.

## Features

- 📌 Fetches commits since the last git tag
- 🏷️ Auto-categorizes into: `Added`, `Fixed`, `Changed`, `Removed`
- 📝 Generates properly formatted CHANGELOG.md
- 🔍 Supports conventional commits and keyword-based detection

## Setup

1. **Download the script:**
   ```bash
   curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.py
   ```

2. **Make it executable:**
   ```bash
   chmod +x changelog.py
   ```

3. **Run in any git repo:**
   ```bash
   ./changelog.py
   ```

## Usage

```bash
# Generate CHANGELOG.md in current directory
./changelog.py

# Output will be saved to CHANGELOG.md
```

## How It Works

The script:
1. Finds the most recent git tag
2. Fetches all commits since that tag
3. Categorizes each commit based on:
   - Conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
   - Keywords in commit messages
4. Generates a formatted CHANGELOG.md

## Example Output

```markdown
# Changelog

## [v1.2.0]

### Added
- New user authentication system (a1b2c3d)
- Dark mode support (e4f5g6h)

### Fixed
- Login redirect bug (i7j8k9l)
- Memory leak in dashboard (m0n1o2p)

### Changed
- Refactored database queries (q3r4s5t)
```

## Requirements

- Python 3.6+
- Git repository with commit history

## Categories

Commits are automatically categorized as:

- **Added** - New features (`feat:`, `add:`, `implement`, etc.)
- **Fixed** - Bug fixes (`fix:`, `bug:`, `resolve`, etc.)
- **Changed** - Modifications (`change:`, `update:`, `refactor:`, etc.)
- **Removed** - Deletions (`remove:`, `delete:`, `cleanup:`, etc.)

## License

MIT