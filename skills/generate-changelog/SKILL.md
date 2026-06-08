---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history since the last tag.
author: SyntaxHQ
version: 1.0.0
---

# generate-changelog

Generates a `CHANGELOG.md` from git commits, categorized by type.

## Usage

```
/generate-changelog [--since <tag-or-ref>]
```

Or run directly:

```bash
bash skills/generate-changelog/changelog.sh
```

## Output

The script creates/updates `CHANGELOG.md` with sections:
- **Added** — new features
- **Fixed** — bug fixes
- **Changed** — modifications
- **Removed** — removed functionality

## Customization

Edit the `CATEGORIES` map in `changelog.sh` to add or change keywords.
