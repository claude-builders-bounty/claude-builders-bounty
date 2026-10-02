---
name: generate-changelog
description: Generate a structured Keep-a-Changelog formatted CHANGELOG.md from git commits since the last tag, categorizing into Added, Fixed, Changed, and Removed.
---

# Generate Changelog Skill

This skill analyzes git commit history since the most recent git tag (or all commits if no tags exist) and generates a structured, Keep-a-Changelog compliant `CHANGELOG.md`.

## Instructions

When the user runs `/generate-changelog` or asks to generate a changelog:

1. Locate or run the included `changelog.sh` script:
   ```bash
   bash changelog.sh
   ```
   Or execute directly with custom options:
   ```bash
   bash changelog.sh --output CHANGELOG.md
   bash changelog.sh --since <tag>
   bash changelog.sh --all
   bash changelog.sh --version "v1.2.0"
   ```

2. The script will:
   - Identify the most recent git tag (using `git describe --tags --abbrev=0`).
   - Extract all non-merge commits between the tag and `HEAD`.
   - Parse conventional commit prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, etc.).
   - Categorize entries into:
     - **Added**: `feat`, `add`, `feature`
     - **Fixed**: `fix`, `bugfix`, `hotfix`
     - **Changed**: `refactor`, `perf`, `style`, `ci`, `build`, `chore`, `docs`, `test`, `update`
     - **Removed**: `revert`, `remove`, `delete`, `deprecate`
   - Format cleanly into `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) standards.
   - Display summary counts of categorized changes.
