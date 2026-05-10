---
name: generate-changelog
description: Auto-generate a structured CHANGELOG.md from git history, categorized by Added/Fixed/Changed/Removed.
---

# Generate Changelog

## Command
`/generate-changelog` or `bash skills/changelog.sh`

## What it does
- Fetches commits since last git tag (or all commits if no tags)
- Categorizes commits by prefix: `feat`/`add` → Added, `fix`/`bug` → Fixed, `remove`/`drop` → Removed, rest → Changed
- Outputs a formatted `CHANGELOG.md` in the project root

## Setup
1. Place `skills/changelog.sh` in your project
2. `chmod +x skills/changelog.sh`
3. Run it!
