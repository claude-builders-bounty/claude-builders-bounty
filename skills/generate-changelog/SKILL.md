---
name: generate-changelog
description: Automatically generates and updates a structured CHANGELOG.md from git history categorized into Added, Fixed, Changed, and Removed following Keep a Changelog standards.
---

# Generate Changelog Skill

This skill analyzes git commits since the last release tag (or repository inception) and builds a clean, structured `CHANGELOG.md` categorized according to the **Keep a Changelog** standard.

## Capabilities
- **Tag Discovery**: Inspects `git describe --tags --abbrev=0` to identify previous releases.
- **Conventional Commits Categorization**:
  - `feat(...)` / `add:` -> **Added**
  - `fix(...)` / `resolve:` -> **Fixed**
  - `refactor(...)` / `chore(...)` / `style(...)` / `perf(...)` -> **Changed**
  - `revert(...)` / `remove(...)` / `deprecate:` -> **Removed**
- **Seamless Update**: Appends new unreleased sections without overwriting historical version release notes.

## Usage
Run the CLI tool or bash script from the root of any git repository:
```bash
python generate_changelog.py
# or
bash changelog.sh
```
