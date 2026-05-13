# generate-changelog — Claude Code Skill

Generate a structured `CHANGELOG.md` from your project's git history with automatic commit categorization.

## Quick Setup

```bash
# 1. Copy the skill to your project
cp -r skills/generate-changelog /path/to/your/project/

# 2. Generate your changelog
python3 skills/generate-changelog/changelog.py
```

## How It Works

The script walks through git commits since the **last tag** (or all commits with `--all`) and categorizes them using conventional commit prefixes:

| Prefix | Category |
|--------|----------|
| `feat:`, `add:` | Added |
| `fix:`, `bug:` | Fixed |
| `refactor:`, `update:` | Changed |
| `remove:`, `drop:` | Removed |
| `doc:`, `readme:` | Documentation |
| `security:` | Security |
| `ci:`, `build:`, `deps:` | Infrastructure |
| `test:` | Tests |
| *(other)* | Miscellaneous |

## Usage

```bash
# Generate CHANGELOG.md in the current repo
python3 skills/generate-changelog/changelog.py

# Specify a repo path
python3 skills/generate-changelog/changelog.py --repo ../my-project

# Custom output file
python3 skills/generate-changelog/changelog.py --output CHANGES.md

# Generate from all commits (ignore tag boundary)
python3 skills/generate-changelog/changelog.py --all

# Set a custom header
python3 skills/generate-changelog/changelog.py --header "v2.0.0"
```

## Claude Code Integration

Add to your `CLAUDE.md`:
```markdown
## Changelog
- To regenerate CHANGELOG.md: `python3 skills/generate-changelog/changelog.py`
- Always update the changelog before a release
```

## Sample Output

```markdown
# Changelog

## [v1.0.0] - 2026-05-13

### Added
- User authentication with OAuth2 (PR #42) (abc1234)
- Dark mode toggle (def5678)

### Fixed
- Login redirect loop on expired sessions (ghi9012)

### Changed
- Upgrade database connection pool (jkl3456)

### Removed
- Deprecated v1 API endpoints (mno7890)
```
