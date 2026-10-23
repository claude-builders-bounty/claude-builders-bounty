---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history since the last tag, categorized into Added, Fixed, Changed, and Removed.
---

# /generate-changelog Skill

When the user invokes `/generate-changelog`:
1. Find the latest git tag using `git describe --tags --abbrev=0` (or fall back to full history if no tag exists).
2. Inspect all non-merge commits since that tag via `git log <tag>..HEAD --oneline --no-merges`.
3. Categorize every commit into **Added**, **Fixed**, **Changed**, or **Removed**.
4. Write the formatted result to `CHANGELOG.md` (or run `bash changelog.sh`).
