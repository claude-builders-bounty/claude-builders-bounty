---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# Generate Changelog

Automatically generates a `CHANGELOG.md` from the project's git history.

## Usage

```bash
/generate-changelog
```

Or run directly:

```bash
bash skills/generate-changelog/changelog.sh
```

## Output

Creates a `CHANGELOG.md` in the project root with commits categorized as:

- **Added** — New features
- **Fixed** — Bug fixes
- **Changed** — Changes in existing functionality
- **Removed** — Removed features
