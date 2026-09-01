---
name: generate-changelog
description: Automatically generates and updates a structured CHANGELOG.md following Keep-a-Changelog standard from git history.
---

# Generate Changelog Skill

This skill inspects the repository's git commit history since the latest tag (or initial commit) and generates an organized `CHANGELOG.md` file.

## Instructions
1. Run the changelog generator script:
   ```bash
   python generate_changelog.py
   # or
   bash changelog.sh
   ```
2. The skill automatically categorizes commits into:
   - `Added` (feat, add)
   - `Fixed` (fix, bugfix)
   - `Changed` (refactor, perf, update)
   - `Removed` (remove, deprecate)
   - `Documentation` (docs)
   - `Maintenance` (chore, ci)
3. Outputs directly into `CHANGELOG.md`.
