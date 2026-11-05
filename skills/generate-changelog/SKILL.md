---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history. Use when the user runs /generate-changelog or asks for a changelog, release notes, or "what changed since the last tag". Auto-categorizes commits into Added/Fixed/Changed/Removed.
---

# /generate-changelog

Create a Keep-a-Changelog-style `CHANGELOG.md` from git history.

## Usage
```bash
# Python (recommended)
python3 generate_changelog.py [OUTPUT] [--version X.Y.Z] [--date YYYY-MM-DD]

# or Bash
bash changelog.sh [OUTPUT]
```

## Behavior
1. Determines the range: `LAST_TAG..HEAD`, or the full history when no tag exists.
2. Classifies each commit subject into **Added / Fixed / Changed / Removed**
   (conventional-commit prefixes first, then keyword heuristics; default `Changed`).
3. Writes a `## [version] - date` section with one bullet per commit (`* subject (sha)`).

## Rules
- Zero third-party dependencies (Python stdlib / bash+git only).
- Never rewrites history or tags; read-only against the repo.
- If no commits are in range, writes a clear "no commits" note.
