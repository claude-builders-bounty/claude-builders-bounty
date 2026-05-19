# Changelog Generator

Generate a structured `CHANGELOG.md` from git history — conventional-commit aware,
fallback keyword matching for plain messages.

## Quick Start

```bash
# 1. Make executable (optional)
chmod +x changelog.sh changelog.py

# 2. Generate changelog
bash changelog.sh
```

## Usage

```bash
# Default: generate CHANGELOG.md from last tag to HEAD
python3 changelog.py

# Custom output path
python3 changelog.py --output docs/CHANGELOG.md

# Specific release tag
python3 changelog.py --tag v2.0.0

# Diff against a previous tag
python3 changelog.py --tag v2.0.0 --prev-tag v1.0.0

# Also works with the bash wrapper
bash changelog.sh -o RELEASE_NOTES.md -t v1.5.0
```

## How It Works

1. Finds the latest git tag (or uses `--tag`)
2. Collects all commits since that tag (or since `--prev-tag`)
3. Parses commit messages:
   - **Conventional commits** → `feat:` → Added, `fix:` → Fixed, `refactor:` → Changed
   - **Plain messages** → keyword matching falls back to detect category
   - **BREAKING CHANGE** → appends `**[BREAKING]**` marker
4. Outputs a `CHANGELOG.md` with sections: Added / Fixed / Changed / Removed / Security

## Supported Commit Prefixes (Conventional Commits)

| Prefix     | Section |
|------------|---------|
| `feat:`    | Added   |
| `fix:`     | Fixed   |
| `refactor:`, `perf:`, `docs:`, `test:`, `chore:`, `ci:`, `build:`, `style:` | Changed |
| `revert:`, `remove:` | Removed |
| `security:` | Security |

## Example Output

```markdown
# Changelog

## [v2.0.0] - 2026-05-19

### Added
- Support for dark mode toggle
- User avatar upload endpoint

### Fixed
- Race condition in session cleanup
- Incorrect timezone rendering on Safari

### Changed
- Refactor auth middleware to use async/await
- Update dependencies to latest stable

### Removed
- Deprecated /api/v1 endpoints
```

## Requirements

- Python 3.8+
- Git (installed and in PATH)
- Must be run from within a git repository
