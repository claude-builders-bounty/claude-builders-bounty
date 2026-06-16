# CHANGELOG Generator

Auto-generates a structured CHANGELOG.md from git commit history.

## Setup (3 steps)

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run: `bash changelog.sh`

## Usage

```bash
# Generate from last tag to HEAD
bash changelog.sh

# Generate from specific tag
bash changelog.sh v1.0.0

# Generate all commits (no tags)
bash changelog.sh
```

## Output Categories

Commits are auto-categorized by prefix:
- **Added**: feat, add, new, implement, introduce
- **Fixed**: fix, bug, patch, resolve, correct
- **Changed**: everything else
- **Removed**: remove, delete, drop, deprecat

## Sample Output

```markdown
# Changelog

## [v1.2.0] - 2026-06-16

### Added
- feat: add user authentication module
- implement dark mode toggle

### Fixed
- fix: resolve memory leak in worker pool
- bug: correct timezone handling

### Changed
- refactor database connection pooling
- update dependencies to latest versions
```
