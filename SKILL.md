---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Use when asked to create release notes or categorize commits since the latest git tag into Added, Fixed, Changed, and Removed.
---

# Generate Changelog

Use this skill when a repository needs a `CHANGELOG.md` created from recent git history.

## Workflow

1. Run `python generate_changelog.py` from the repository root, or `bash changelog.sh` on Unix-like systems.
2. Review the generated `CHANGELOG.md` for category fit and wording.
3. Mention the detected range, last tag if present, and commit count in your response.

The script reads commits since the latest git tag, or all commits when no tags exist. It groups commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
