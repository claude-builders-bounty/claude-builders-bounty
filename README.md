# generate-changelog

Generate a structured CHANGELOG.md from your project's git history. Automatically categorizes commits into **Added**, **Fixed**, **Changed**, and **Removed** sections using conventional commit parsing and keyword analysis.

## Setup

1. Copy `changelog.sh` and `categorize.py` into your project
2. Make executable: `chmod +x changelog.sh`
3. Run: `bash changelog.sh`

## Usage

```bash
# Generate changelog from last tag to HEAD
bash changelog.sh

# Generate from a specific tag
bash changelog.sh --since v1.2.0

# Output to a custom file
bash changelog.sh --output CHANGES.md

# Label as unreleased
bash changelog.sh --unreleased
```

## How It Works

- Parses conventional commits (`feat:`, `fix:`, `refactor:`, etc.)
- Falls back to keyword analysis for non-conventional messages
- Appends new sections to existing CHANGELOG.md without overwriting history
- Groups commits by category in standard Keep a Changelog format

## Requirements

- Git
- Python 3.8+
- No external dependencies (stdlib only)

## Example Output

```markdown
# Changelog

## [v1.0.0 → HEAD] - 2026-05-20

### Added

- Implement user authentication via OAuth2
- Add dark mode toggle to settings

### Fixed

- Resolve memory leak in WebSocket handler
- Fix pagination offset calculation

### Changed

- Refactor database connection pooling
- Update dependencies to latest versions

### Removed

- Remove deprecated v1 API endpoints
```
