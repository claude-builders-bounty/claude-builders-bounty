---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a git repository's commit history, using the latest git tag as the default lower bound and categorizing commits into Added, Fixed, Changed, and Removed.
---

# Generate Changelog

Use this skill when a user asks to create or refresh a `CHANGELOG.md` from git history.

## Workflow

1. Run `bash generate-changelog/scripts/changelog.sh --stdout` to preview the generated changelog.
2. If the preview is correct, run `bash generate-changelog/scripts/changelog.sh` to write `CHANGELOG.md`.
3. Review the categories and edit only for product context that cannot be inferred from commit messages.

## Behavior

- The script fetches tags when possible, then uses commits since the latest tag.
- If there are no tags, it includes the full repository history.
- Conventional commit prefixes are mapped as:
  - `feat` or `feature` -> `Added`
  - `fix`, `bugfix`, or `hotfix` -> `Fixed`
  - `remove`, `delete`, `drop`, or `deprecate` -> `Removed`
  - `docs`, `refactor`, `style`, `perf`, `test`, `build`, `ci`, `chore`, or `revert` -> `Changed`
- Unrecognized commits are placed in `Changed` unless their subject contains a strong add/fix/remove keyword.

## Useful Commands

```bash
bash changelog.sh
bash changelog.sh --stdout
bash changelog.sh --from v1.2.0 --output CHANGELOG.md
bash generate-changelog/scripts/changelog.sh --stdout
bash generate-changelog/scripts/test-changelog.sh
```
