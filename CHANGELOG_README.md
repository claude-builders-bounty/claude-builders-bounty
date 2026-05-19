# generate-changelog.sh

Generate a structured `CHANGELOG.md` from git history with a single command.

## Installation

```bash
# 1. Copy to your project
cp generate-changelog.sh /path/to/your/project/

# 2. Make it executable  
chmod +x generate-changelog.sh
```

## Usage

```bash
# Generate changelog since the last git tag
bash generate-changelog.sh

# Or specify a starting tag
bash generate-changelog.sh v1.0.0
```

## Output

Commits are auto-categorized into:
- **Added** — feat, add, new, introduce, implement
- **Fixed** — fix, bug, patch, resolve, hotfix  
- **Changed** — refactor, change, update, improve, perf, style
- **Removed** — remove, drop, delete, deprecate

Example output:
```markdown
# Changelog

## [v1.0.0 → HEAD] — 2025-06-15

### Added
- Implement OAuth2 login flow
- Add dark mode support

### Fixed
- Fix memory leak in WebSocket handler

### Changed
- Refactor auth middleware for better error handling
```

## How it works

1. Fetches commits since the latest git tag (or all commits if no tags)
2. Classifies by Conventional Commits prefix (feat:, fix:, etc.) and message keywords
3. Outputs structured markdown to `CHANGELOG.md`
