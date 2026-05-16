---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
allowed-tools: Bash(git:*), Bash(./changelog.sh:*)
---

# Generate Changelog

Use this skill when the user asks to generate or refresh a changelog from repository history.

## Instructions

1. Confirm the current working directory is a git repository.
2. Run:

   ```bash
   ./changelog.sh
   ```

3. Review the generated `CHANGELOG.md` sections:
   - Added
   - Fixed
   - Changed
   - Removed

## Options

- For a specific release heading:

  ```bash
  ./changelog.sh --version 1.2.0
  ```

- To force a starting ref:

  ```bash
  ./changelog.sh --since v1.1.0
  ```

- To target another repo:

  ```bash
  ./changelog.sh --repo ../project --output ../project/CHANGELOG.md
  ```

## Quality bar

- Do not invent changes that are not in git history.
- Keep generated bullets concise.
- If the repo uses non-conventional commits, keep unknown items under `Changed` rather than omitting them.
