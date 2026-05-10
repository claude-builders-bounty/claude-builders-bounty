---
name: generate-changelog
description: Auto-generate a structured CHANGELOG.md from git history
triggers:
  - /generate-changelog
  - /changelog
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from git commit history, auto-categorizing changes into **Added**, **Fixed**, **Changed**, and **Removed** sections.

## Usage

```bash
# Generate changelog since last tag
bash changelog.sh

# Generate changelog for a specific range
bash changelog.sh v1.0.0..v1.1.0

# Generate and append to existing CHANGELOG.md
bash changelog.sh --append
```

## How it works

1. Finds the latest git tag (or uses specified range)
2. Extracts all commits in the range
3. Categorizes each commit by conventional commit prefix or keyword detection
4. Generates a formatted `CHANGELOG.md` with:
   - Version header with date
   - Grouped changes by category
   - Commit hash links
   - Author attribution

## Commit Classification Rules

| Pattern | Category |
|---------|----------|
| `feat:`, `add`, `new`, `create`, `implement` | Added |
| `fix:`, `bug`, `patch`, `resolve`, `correct` | Fixed |
| `refactor:`, `update:`, `change:`, `modify`, `improve`, `perf:` | Changed |
| `remove:`, `delete:`, `deprecate:`, `drop` | Removed |
| `docs:`, `doc:` | Documentation |
| `chore:`, `ci:`, `build:`, `test:` | Maintenance |

## Requirements

- Git repository with at least one commit
- Bash 4.0+
