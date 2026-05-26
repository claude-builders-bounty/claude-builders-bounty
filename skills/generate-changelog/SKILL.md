---
name: generate-changelog
description: Generate a structured CHANGELOG.md file based on commits in the git history since the last release tag.
---

# Generate Changelog Skill

This skill teaches Claude how to automatically generate or update a structured `CHANGELOG.md` file based on a project's recent git history.

## Quick Start / Usage

When you want to document recent changes, run:

```bash
bash changelog.sh
```

## Categorization Rules

The script automatically classifies commits into the following categories:
- **Added**: Commits starting with `feat`, `add`, `new`, `create`, or `implement` (case-insensitive).
- **Fixed**: Commits starting with `fix`, `bug`, `patch`, or `resolve` (case-insensitive).
- **Removed**: Commits starting with `remove`, `delete`, or `rm` (case-insensitive).
- **Changed**: All other commits.

## Output Format

The output follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:
- Grouped by release version/Unreleased and Date.
- Bullet points containing the commit subject and commit hash.
