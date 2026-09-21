---
name: generate-changelog
description: Automatically generates or updates a structured Keep a Changelog compliant CHANGELOG.md from git commits since the last tag.
triggers:
  - "/generate-changelog"
  - "generate changelog"
  - "update changelog"
---

# Generate Changelog Skill

This skill analyzes git commit history since the most recent git tag (or from initial commit) and generates or prepends an entry to `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) standards.

## Usage

When the user runs `/generate-changelog` or asks to generate a changelog:

1. Locate the project's root git directory.
2. Execute the bundled script:
   ```bash
   bash skills/changelog-generator/changelog.sh [OUTPUT_FILE] [LAST_TAG] [VERSION]
   ```
   Or run directly:
   ```bash
   bash changelog.sh
   ```
3. The script inspects commits using `git log`, strips conventional prefixes (`feat:`, `fix:`, `refactor:`, `remove:`, `sec:`), and organizes into:
   - `### Added`
   - `### Fixed`
   - `### Changed`
   - `### Removed`
   - `### Security`
4. Summarize the added release notes to the user.
