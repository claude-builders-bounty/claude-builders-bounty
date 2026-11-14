---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from project git history since the last release tag.
---

# Generate Changelog Skill

This skill analyzes git commits since the last release tag and generates or updates a clean, structured `CHANGELOG.md` adhering to the [Keep a Changelog](https://keepachangelog.com/) standard.

## Instructions

When the user runs `/generate-changelog` or asks to generate/update the changelog:

1. Execute the changelog generation script:
   ```bash
   bash changelog.sh
   ```
2. The script automatically:
   - Finds the latest git tag (`git describe --tags --abbrev=0`).
   - Gathers commits since that tag.
   - Categorizes into: `Added`, `Fixed`, `Changed`, `Removed`.
   - Formats and prepends entries to `CHANGELOG.md`.
