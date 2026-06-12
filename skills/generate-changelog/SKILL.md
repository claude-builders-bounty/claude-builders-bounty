---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when a project needs a release changelog generated from git history.

## Workflow

1. Run `bash skills/generate-changelog/scripts/changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md`.
3. Commit the changelog with the release changes.

The script finds the latest git tag with `git describe --tags --abbrev=0`, reads commits since that tag, categorizes them into `Added`, `Fixed`, `Changed`, and `Removed`, and writes a Keep a Changelog-style `CHANGELOG.md`.

If no tag exists, the script uses the full commit history.
