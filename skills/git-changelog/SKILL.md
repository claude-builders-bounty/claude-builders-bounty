---
name: git-changelog
description: Generate a structured CHANGELOG.md from git history. Use when you need to create or update a project's changelog, or when the user asks about changelog generation, release notes, or commit history summarization. Triggers on phrases like "generate changelog", "create changelog", "update changelog", "changelog from git", or "/generate-changelog".
---

# Git Changelog Generator

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Quick Start

Run the changelog generator script:

```bash
/path/to/skill/scripts/generate_changelog.py [OPTIONS]
```

Or use the skill directly:

```
/generate-changelog
```

## How It Works

1. Fetches all commits since the last git tag (or from the beginning if no tags exist)
2. Auto-categorizes commits based on conventional commit prefixes or keywords:
   - `Added` / `feat` / `feature` → **Added**
   - `Fixed` / `fix` / `bugfix` → **Fixed**
   - `Changed` / `update` / `refactor` / `improve` → **Changed**
   - `Removed` / `delete` / `deprecate` → **Removed**
3. Generates a properly formatted CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format

## Categorization Rules

Commits are categorized by analyzing the commit message:

| Prefix/Keyword | Category |
|----------------|----------|
| `feat:`, `feature:`, `add:`, `Added:` | Added |
| `fix:`, `bugfix:`, `Fixed:`, `bug:` | Fixed |
| `update:`, `refactor:`, `change:`, `Changed:`, `improve:` | Changed |
| `remove:`, `delete:`, `deprecate:`, `Removed:` | Removed |

Commits without recognizable prefixes are placed in a "Other changes" section.

## Script Options

```
generate_changelog.py [OPTIONS]

Options:
  -o, --output FILE    Output file path (default: CHANGELOG.md)
  -t, --tag TAG        Generate changelog from this tag (default: last tag)
  -a, --all            Generate changelog for all commits (ignore tags)
  -r, --repo PATH      Path to git repository (default: current directory)
  --no-links           Don't generate links to commits
  --version VERSION    Specify version for the new release
  -h, --help           Show help message
```

## Example Output

```markdown
## [Unreleased]

## [1.0.0] - 2024-01-15

### Added
- Add new user authentication system
- Add password reset functionality
- Add email validation on signup

### Fixed
- Fix login redirect loop
- Fix timezone issue in date picker

### Changed
- Update dependencies to latest versions
- Refactor database connection pooling

### Removed
- Remove deprecated legacy API endpoints
```

## Integration with Release Workflow

The script can be integrated into CI/CD pipelines:

```bash
# Generate changelog before release
python scripts/generate_changelog.py --version $NEW_VERSION

# Or in GitHub Actions
- name: Generate Changelog
  run: python scripts/generate_changelog.py --version ${{ github.event.inputs.version }}
```

## Script Location

The generator script is located at:
- `scripts/generate_changelog.py` (within the skill directory)

Execute it directly or use the skill trigger.