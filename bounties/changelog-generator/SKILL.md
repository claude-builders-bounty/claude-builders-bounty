---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# Generate Changelog

Generate or update a structured `CHANGELOG.md` based on the project's git history.

## Usage

`` /generate-changelog ``

or

```
bash changelog.sh
python changelog.py
```

## Behavior

1. Finds the last git tag as a version anchor
2. Fetches all commits since that tag (or all commits if no tags exist)
3. Categorizes each commit:
   - **Added**: `feat:`, `add`, `feature`, `new`
   - **Fixed**: `fix:`, `bug`, `hotfix`, `patch`, `resolve`
   - **Removed**: `remove`, `delete`, `drop`, `deprecate`
   - **Changed**: everything else (chore, refactor, docs, etc.)
4. Outputs a properly formatted `CHANGELOG.md` with:
   - Version number (auto-incremented from last tag)
   - ISO date
   - Categorized commit list with short hashes

## Options

- Custom output path: `python changelog.py output.md`
- Default output: `CHANGELOG.md` in the current directory

## Example Output

```markdown
# Changelog

## [v1.2.1] - 2026-05-31

### Added
- Add user authentication module (a1b2c3d)

### Fixed
- Fix login redirect loop (e4f5g6h)

### Changed
- Refactor database connection pool (i7j8k9l)
```

## Requirements

- Git repository with commits
- Python 3.6+ or Bash 4.0+
