---
name: generate-changelog
description: Automatically inspects git commit history since the last tag and generates a structured CHANGELOG.md adhering to Keep a Changelog.
triggers:
  - "/generate-changelog"
  - "generate changelog"
  - "update changelog"
---

# Generate Changelog Skill

This skill parses git commits since the most recent release tag, auto-categorizes them into `Added`, `Fixed`, `Changed`, `Removed`, and generates or updates a structured `CHANGELOG.md`.

## Execution Steps

1. Detect the repository root and identify the last git tag:
   ```bash
   git describe --tags --abbrev=0 2>/dev/null || echo "INITIAL"
   ```

2. Run the bundled changelog generator:
   ```bash
   bash changelog.sh CHANGELOG.md
   ```

3. Review the generated `CHANGELOG.md` and present the summary to the user.
