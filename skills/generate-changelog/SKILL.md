---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag
---

# Generate Changelog

## When to use
When the user asks for a changelog, release notes, or runs `/generate-changelog`.

## Steps
1. Run from the repo root:
   ```bash
   bash changelog.sh . CHANGELOG.md
   ```
2. Review `CHANGELOG.md` sections: Added / Fixed / Changed / Removed.
3. If no git tags exist, the script uses full history.

## Rules
- Prefer commit subjects; no merge commits.
- Keep existing release headers if appending manually after generation.
