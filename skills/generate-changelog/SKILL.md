---
name: generate-changelog
description: Automatically generates a structured Keep-a-Changelog CHANGELOG.md from git history since the latest release tag.
---

# Generate Changelog Skill

Use this skill whenever you need to produce a clean, categorized `CHANGELOG.md` from git commits.

## Workflow

1. Execute the changelog generator script:
   ```bash
   bash changelog.sh
   # or
   python changelog.py
   ```

2. The script:
   - Identifies the latest git tag (`git describe --tags --abbrev=0`).
   - Parses commits between `tag..HEAD`.
   - Automatically groups changes into `Added`, `Fixed`, `Changed`, and `Removed`.
   - Writes the result to `CHANGELOG.md`.

3. Review the generated `CHANGELOG.md` and commit.
