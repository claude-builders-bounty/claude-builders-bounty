---
name: generate-changelog
description: Generate a structured Keep a Changelog compliant CHANGELOG.md from git history since the last release tag.
triggers:
  - "/generate-changelog"
  - "generate changelog"
  - "update changelog"
---

# Generate Changelog Skill

Automatically parses commit history from the latest git tag to `HEAD`, auto-categorizes commits into standard conventional categories (**Added**, **Fixed**, **Changed**, **Removed**, **Breaking Changes**), and writes or updates `CHANGELOG.md`.

## When to Run
- Run whenever preparing a release or after merging pull requests.
- Invoked via `/generate-changelog` or `bash changelog.sh`.

## Workflow
1. Execute the changelog generator script:
   ```bash
   bash changelog.sh
   ```
2. To specify a specific version tag name or custom release title:
   ```bash
   bash changelog.sh --version "v1.2.0"
   ```
3. To generate changelog between specific git tags:
   ```bash
   bash changelog.sh --since "v1.0.0" --until "v1.1.0"
   ```
4. Review the generated `CHANGELOG.md` file and stage it for commit.
