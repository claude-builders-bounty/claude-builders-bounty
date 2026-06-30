# Git Changelog Generator

A Claude Code skill that generates a structured `CHANGELOG.md` from a project's git history.

## Usage

```bash
# Generate CHANGELOG from last tag to HEAD
bash skills/changelog.sh

# Specify a custom tag
bash skills/changelog.sh --tag v1.0.0

# Custom output file
bash skills/changelog.sh --output docs/CHANGELOG.md
```

## How it works

1. Fetches commits since the last git tag (or all commits if no tags exist)
2. Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
3. Outputs a properly formatted `CHANGELOG.md` with semantic versioning conventions

## Categorization Rules

| Category | Conventional Commit Prefix |
|----------|--------------------------|
| **Added** | `feat:`, `feature:`, `add:`, `new:`, `implement:`, `create:`, `support:` |
| **Fixed** | `fix:`, `bugfix:`, `hotfix:`, `patch:`, `correct:`, `resolve:` |
| **Removed** | `remove:`, `delete:`, `deprecate:`, `drop:` |
| **Changed** | Everything else |

## Requirements

- `bash` (any modern version)
- `git` repository with conventional commit messages (recommended)
