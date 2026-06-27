---
name: generate-changelog
description: Generate structured CHANGELOG.md from git history since last tag
---

# Generate Changelog

Run `/generate-changelog` or `bash scripts/changelog.sh`.

## Behavior
- Fetches commits since the last git tag (or all if none)
- Categories: Added / Fixed / Changed / Removed
- Writes formatted CHANGELOG.md
