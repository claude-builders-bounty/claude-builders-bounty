---
name: generate-changelog
description: Automatically parse git history and generate a structured CHANGELOG.md categorized into Added, Fixed, Changed, and Removed.
---

# Git CHANGELOG Generator

An automated tool to parse repository commits since the latest git tag and format an updated `CHANGELOG.md` adhering to the Keep a Changelog convention.

## Quickstart (3 steps)

1. Ensure the script is executable:
   ```bash
   chmod +x changelog.sh changelog.py
   ```
2. Run via Bash or Python:
   ```bash
   ./changelog.sh
   # or
   python3 changelog.py
   ```
3. Inspect the updated `CHANGELOG.md`.

## Features
- **Tag-Aware:** Automatically fetches commits since the latest git tag (or from inception).
- **Conventional Commits:** Groups commits into `Added`, `Fixed`, `Changed`, `Removed`, and `Maintenance`.
- **Author & Hash Attribution:** Includes commit hash references and author names.
