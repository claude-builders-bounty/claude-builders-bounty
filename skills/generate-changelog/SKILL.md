# SKILL: Generate Changelog

Trigger: User asks to generate a changelog, update changelog, or create release notes.

## Commands

```bash
# Generate CHANGELOG.md in current repo
/skills/generate-changelog/changelog.sh

# Generate for a specific repo
/skills/generate-changelog/changelog.sh /path/to/repo

# Preview without writing file
python3 /skills/generate-changelog/generate-changelog.py --dry-run

# Start from a specific tag
python3 /skills/generate-changelog/generate-changelog.py --since v1.0.0
```

## What it does

1. Finds the latest git tag in the repo (or uses --since)
2. Collects all commits since that tag
3. Categorizes each commit:
   - **Added** → feat, add, introduce, new, implement
   - **Fixed** → fix, bugfix, resolve, patch, hotfix
   - **Changed** → refactor, update, modify, improve, enhance
   - **Removed** → remove, delete, drop, deprecate
4. Writes a formatted `CHANGELOG.md`

## Requirements

- Python 3.8+
- Git repository with at least one commit

## Output Example

```markdown
# Changelog
All notable changes to `my-project` will be documented in this file.

## [v1.0.0 → HEAD] — 2026-05-12

### Added
- Add user authentication flow (`a1b2c3d`)
- Implement dark mode toggle (`e4f5g6h`)

### Fixed
- Fix login redirect loop (`i7j8k9l`)
```
