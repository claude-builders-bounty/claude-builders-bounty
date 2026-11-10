---
name: generate-changelog
description: Automatically generate a structured CHANGELOG.md from git history since the last git tag, categorized into Added, Fixed, Changed, and Removed. Triggered via /generate-changelog or bash changelog.sh.
---

# `/generate-changelog` — Structured Git Changelog Skill

When the user invokes `/generate-changelog` (or asks to generate/update `CHANGELOG.md`):

## Execution Steps

1. **Locate Repository & Latest Git Tag**:
   - Run `bash changelog.sh` (or `python3 generate_changelog.py .`) in the target repository root.
   - The script automatically inspects `git describe --tags --abbrev=0` to find the most recent git tag (or falls back to full commit history if no tags exist).

2. **Automatic Categorization (`Added` / `Fixed` / `Changed` / `Removed`)**:
   - Commits are classified deterministically by Conventional Commit prefixes and semantic verbs:
     - **`Added`**: `feat`, `feature`, `add`, `init`, or commits introducing new capabilities.
     - **`Fixed`**: `fix`, `bugfix`, `hotfix`, `sec`, or commits resolving defects.
     - **`Changed`**: `refactor`, `perf`, `docs`, `chore`, `update`, or behavioral improvements.
     - **`Removed`**: `remove`, `delete`, `drop`, `deprecate`, or retired features.

3. **Output Verification**:
   - Writes a Keep-a-Changelog compliant `CHANGELOG.md` and displays a concise summary of categorized commits to the user.
