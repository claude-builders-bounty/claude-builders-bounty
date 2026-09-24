---
name: generate-changelog
description: Automatically generates a structured, Keep a Changelog compliant CHANGELOG.md from git history since the last tag.
---

# Generate Changelog Skill

Inspects the repository's git commits since the last release tag (or initial commit) and categorizes changes into `Added`, `Fixed`, `Changed`, and `Removed`.

## Usage
Run directly from terminal or via Claude Code command:
```bash
bash changelog.sh [version] [output_file]
```
Examples:
- `bash changelog.sh` -> Generates notes for `[Unreleased]`
- `bash changelog.sh v1.2.0` -> Generates notes for release `[v1.2.0]`
