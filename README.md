# Changelog Generator

A bash script that generates a structured `CHANGELOG.md` from git history.

## Quick Start

1. Copy `changelog.sh` to your project root
2. Run: `bash changelog.sh`
3. Commit the generated `CHANGELOG.md`

## Usage

```bash
# Generate from last git tag
bash changelog.sh

# Generate from specific tag
bash changelog.sh v1.0.0

# Generate last 50 commits
bash changelog.sh HEAD~50
```

## Output Format

Commits are auto-categorized:
- **Added** — New features
- **Fixed** — Bug fixes
- **Changed** — Refactors and modifications
- **Removed** — Deprecations and removals

## Requirements

- Bash 4.0+
- Git
