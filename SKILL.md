---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, "generate a changelog", or a release note draft from the current repository history.

## Workflow

1. Run the repository-local script:

   ```bash
   bash changelog.sh
   ```

2. Review the generated `CHANGELOG.md` before committing it.

3. If the project has no tags, the script falls back to all commits reachable from `HEAD`.

## Output Format

The script writes a Keep a Changelog-style draft with these sections:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

Commits are grouped from Conventional Commit prefixes and common release keywords. Uncategorized commits are placed under `Changed` so no work is silently dropped.
