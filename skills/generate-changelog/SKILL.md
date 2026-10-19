---
name: generate-changelog
description: Generate a structured CHANGELOG.md categorized by Added, Fixed, Changed, and Removed from git history since the last release tag.
---

# Generate Changelog Skill

This skill analyzes recent git commits and produces a Keep-a-Changelog compliant release summary.

## Usage
Run `/generate-changelog` or call `scripts/changelog.sh`.

## Workflow
1. Detects the latest semver tag (`git describe --tags --abbrev=0`).
2. Extracts all commit messages since that tag:
   ```bash
   git log ${LATEST_TAG}..HEAD --pretty=format:"%s (%h)"
   ```
3. Parses conventional commit prefixes:
   - `feat:` -> **Added**
   - `fix:`, `bug:` -> **Fixed**
   - `refactor:`, `perf:`, `chore:` -> **Changed**
   - `deprecate:`, `remove:` -> **Removed**
4. Generates or updates `CHANGELOG.md` with release date and version header.
