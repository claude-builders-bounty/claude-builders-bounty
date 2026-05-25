---
name: generate-changelog
summary: Generate a structured CHANGELOG from git history.
---

# Generate Changelog

Run `bash bounty-solutions/changelog-generator/changelog.sh` in a git repo.

Behavior:
- Uses commits since the last git tag
- Categorizes commits into Added / Fixed / Changed / Removed
- Writes `CHANGELOG.md`

Usage:
- `bash bounty-solutions/changelog-generator/changelog.sh`
- `bash bounty-solutions/changelog-generator/changelog.sh v1.2.3..HEAD`
