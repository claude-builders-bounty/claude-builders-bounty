# SKILL: Generate CHANGELOG from Git History

Generates a structured CHANGELOG.md from git history since the last tag, using Conventional Commits format.

## Trigger Phrases

- "generate changelog"
- "changelog from git"
- "create CHANGELOG.md"
- "update changelog"
- "changelog since last tag"
- "export git history to changelog"

## Usage

```bash
# Generate CHANGELOG.md for commits since last tag
python changelog.py

# Custom output file
python changelog.py -o CHANGELOG.md

# Include ALL commits (no tag filter)
python changelog.py --all

# List available tags
python changelog.py --list-tags

# Dry run — print to stdout
python changelog.py --dry-run
```

## Features

- **Conventional Commits parsing**: Automatically categorizes commits into Added / Fixed / Changed / Removed
- **Smart detection**: Recognizes `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, etc.
- **Fallback heuristics**: Also catches keywords like "add", "fix", "remove" in commit messages
- **Tag-aware**: Filters commits since last git tag by default
- **Multiple output modes**: Write to file, stdout, or dry-run
- **Previous releases**: Includes links to previous tag versions

## Example Output

```markdown
# Changelog

## [v1.2.0] - 2026-05-19

### Added
- New user authentication module (#123)
- Dark mode support (#456)

### Fixed
- Login redirect loop bug (#789)

### Changed
- Updated dependencies to latest versions

---

*Generated on 2026-05-19 12:00:00*
```

## Requirements

- Python 3.7+
- Git repository with commits

## Installation

1. Copy `changelog.py` to your project
2. Run `python changelog.py` to generate CHANGELOG.md
3. Review and commit the generated file

---

*Part of claude-builders-bounty · Issue #1 · $50 bounty*
