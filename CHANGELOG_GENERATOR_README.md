# CHANGELOG Generator

Automatically generates a structured `CHANGELOG.md` from git history.

## Quick Start

1. Copy the script to your project root:
   - **Python**: `changelog_generator.py`
   - **Bash**: `changelog.sh`
   - **PowerShell**: `changelog.ps1`

2. Run the script:
   - Python: `python3 changelog_generator.py`
   - Bash: `bash changelog.sh`
   - PowerShell: `powershell -ExecutionPolicy Bypass -File changelog.ps1`

3. Review the generated `CHANGELOG.md`

## Features

- ✅ Fetches commits since the last git tag
- ✅ Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- ✅ Outputs properly formatted `CHANGELOG.md`
- ✅ Works with conventional commit messages
- ✅ Available in Python, Bash, and PowerShell

## Sample Output

```markdown
# Changelog

## [v1.0.0] - 2026-08-18

### Added
- Add user authentication feature
- Implement dark mode toggle

### Fixed
- Fix memory leak in image processing
- Correct typo in README

### Changed
- Update dependencies to latest versions
- Refactor database connection logic

### Removed
- Remove deprecated API endpoints
```

## Commit Categorization

Commits are categorized based on keywords:

- **Added**: `add`, `added`, `feat:`, `feature`, `new`, `create`, `implement`
- **Fixed**: `fix`, `fixed`, `fix:`, `bug`, `bugfix`, `resolve`, `correct`, `patch`
- **Removed**: `remove`, `removed`, `remove:`, `delete`, `deleted`, `deprecate`
- **Changed**: `change`, `changed`, `change:`, `update`, `updated`, `modify`, `refactor` (default)

## Requirements

- Git installed and initialized
- Python 3.6+ (for Python version)
- Bash (for Bash version)
- PowerShell (for PowerShell version)