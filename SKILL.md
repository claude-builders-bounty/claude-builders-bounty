---
name: changelog-generator
description: Generate a structured CHANGELOG.md from a project's git history with conventional-commit categorization.
---

# changelog-generator

A Claude Code skill that generates a structured `CHANGELOG.md` from a project's git history. Automatically categorizes commits into **Added**, **Fixed**, **Changed**, and **Removed** sections based on conventional commit prefixes.

## Usage

In any git repository, run:

```
python /path/to/changelog.py
```

Or with options:

```
python /path/to/changelog.py --output CHANGELOG.md --repo /path/to/repo
```

## How it works

1. Finds the most recent git tag (or the very first commit)
2. Collects all commits since that tag
3. Parses commit messages using conventional-commit format
4. Categorizes into: Added, Fixed, Changed, Removed
5. Writes a clean `CHANGELOG.md`

### Conventional commit prefixes recognized

| Category  | Prefixes |
|-----------|----------|
| **Added**     | `feat:`, `feature:`, `add:` |
| **Fixed**     | `fix:`, `bug:`, `hotfix:`, `bugfix:` |
| **Changed**   | `refactor:`, `perf:`, `chore:`, `style:`, `docs:`, `test:`, `update:`, `improve:`, `upgrade:`, `migrate:` |
| **Removed**   | `remove:`, `revert:`, `delete:`, `deprecate:` |

### Auto-skipped commits

Merge commits, release bumps, and dependency-only changes are automatically filtered out.

## Output format

```markdown
# Changelog

> Generated on 2025-06-14

## Added
- **New feature description** (abc1234) - Author Name

## Fixed
- **Bug fix description** (def5678) - Author Name
```
