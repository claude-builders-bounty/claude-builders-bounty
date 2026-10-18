---
name: generate-changelog
description: Automatically generate a structured, categorized CHANGELOG.md from git commit history.
---

# Generate Changelog Skill

Automates changelog maintenance by inspecting git history since the last release tag and categorizing commits into **Added**, **Fixed**, **Changed**, and **Removed** sections conforming to Keep A Changelog standards.

## Usage in Claude Code / Antigravity

Invoke via:
```bash
/generate-changelog
```
Or execute directly:
```bash
bash changelog.sh
```

## Options
- `--from <tag|sha>`: Starting reference (defaults to latest git tag).
- `--to <ref>`: Ending reference (defaults to `HEAD`).
- `--output <path>`: Custom output markdown path (defaults to `CHANGELOG.md`).
- `--stdout`: Print formatted changelog directly to the console.
