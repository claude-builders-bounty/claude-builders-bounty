# 📋 Changelog Generator

Automatically generates a structured `CHANGELOG.md` from your project's git history.

## Quick Start

```bash
# 1. Copy the script to your project
cp changelog.sh /path/to/your/project/

# 2. Generate your changelog
cd /path/to/your/project && python3 changelog.sh
```

**Done.** Open `CHANGELOG.md` to see the results.

## Usage

```bash
# Generate changelog since the last git tag (auto-detected)
python3 changelog.sh

# Generate changelog from a specific tag
python3 changelog.sh --from v1.0.0

# Output to a custom file
python3 changelog.sh --output HISTORY.md

# Print to stdout
python3 changelog.sh --stdout
```

## Features

- **Auto-categorization** — Commits are sorted into: `Added` / `Fixed` / `Changed` / `Removed` / `Documentation` / `Testing` / `CI/CD`
- **Conventional commit aware** — Recognizes `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `ci:` prefixes
- **Emoji support** — Also categorizes by leading emoji (✨ → Added, 🐛 → Fixed, etc.)
- **Link to commits** — Each entry links to the commit on GitHub
- **Auto-version** — Uses the last git tag as the version number

## Requirements

- Python 3.7+
- Git (any version)
- Works on macOS, Linux, and WSL

## Example Output

```
# Changelog

## [v1.0.0] — 2026-05-13

### 🚀 Added
- Implement cross-session memory retrieval (#42) (abc1234)
- Add user authentication module (def5678)

### 🐛 Fixed
- Fix null pointer in session handler (ghi9012)
- Resolve memory leak in long-running graphs (jkl3456)

### 🔄 Changed
- Refactor API client to use async/await (mno7890)
- Update dependencies to latest versions (pqr1234)

### 🗑️ Removed
- Drop deprecated v1 API endpoints (stu5678)
```

## License

MIT
