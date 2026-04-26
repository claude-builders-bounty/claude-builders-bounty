---
name: changelog-generator
description: Generate structured CHANGELOG.md from git commit history with automatic categorization
homepage: https://github.com/davidweb3-ctrl/claude-builders-bounty/tree/main/skills/changelog-generator
metadata:
  {
    "openclaw":
      {
        "emoji": "📝",
        "requires": { "bins": ["git", "bash"] },
      },
  }
---

# Changelog Generator

Generate a structured `CHANGELOG.md` from a project's git history.

## Quick start

```bash
./skills/changelog-generator/changelog.sh
```

## What it does

1. Finds the last git tag (or first commit)
2. Gets all commits since that point
3. Categorizes into: Added / Fixed / Changed / Removed
4. Generates a properly formatted CHANGELOG.md

## Categorization rules

| Commit prefix | Category |
|--------------|----------|
| `feat:`, `add:`, `implement:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `refactor:`, `update:`, `improve:` | Changed |
| `remove:`, `delete:`, `drop:` | Removed |

## Example

```bash
# In your repo root
./skills/changelog-generator/changelog.sh

# Output: CHANGELOG.md
```

## Output format

Follows [Keep a Changelog](https://keepachangelog.com/) standard.
