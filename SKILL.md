---
name: generate-changelog
description: Automatically generates and updates a structured CHANGELOG.md from git commit history since the last release tag.
---

# Generate Changelog Skill

Use this skill to extract conventional commits from git history and format them into a standard Keep a Changelog markdown file.

## Usage
Run directly from terminal or bash:
```bash
bash changelog.sh
```
or
```bash
python generate_changelog.py
```

## Features
- Fetches all commits between the latest git tag and `HEAD`.
- Parses Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`, `remove:`).
- Categorizes automatically into:
  - `Added`
  - `Fixed`
  - `Changed`
  - `Removed`
- Preserves existing changelog entries and prepends the new section cleanly.
