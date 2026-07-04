# 📋 Changelog Generator

> **Bounty #1** — Auto-generate a structured `CHANGELOG.md` from git history.

## Setup

```bash
# 1. Copy the script to your project
cp changelog.sh /path/to/your/project/

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it
bash changelog.sh
```

## Usage

```bash
# Generate CHANGELOG.md in current directory
bash changelog.sh

# Custom output path
bash changelog.sh --output docs/CHANGELOG.md

# From a specific tag
bash changelog.sh --since v1.0.0

# From a different repo path
bash changelog.sh --repo /path/to/project
```

## How it works

The script parses git history and categorizes commits by conventional commit prefix:

| Prefix       | Category        | Emoji |
|-------------|-----------------|-------|
| `feat:`     | **Added**       | ✨    |
| `fix:`      | **Fixed**       | 🐛    |
| `refactor:` | **Changed**     | ♻️    |
| `docs:`     | **Documentation** | 📝  |
| `style:`    | **Styling**     | 💄    |
| `test:`     | **Testing**     | 🧪    |
| `chore:`    | **Maintenance** | 🔧    |
| `revert:`   | **Removed**     | ⏪    |

Falls back to a flat list if no conventional commits are found.

## Sample Output

```markdown
# Changelog

## [v2.1.0] - 2026-07-04

### ✨ Added
- User authentication with OAuth2
- Dark mode toggle
- Export to CSV

### 🐛 Fixed
- Login crash on Safari
- Memory leak in WebSocket handler
```
