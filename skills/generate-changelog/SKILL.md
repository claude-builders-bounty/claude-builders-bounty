---
name: generate-changelog
description: Generates a categorized CHANGELOG.md (Added, Fixed, Changed, Removed) from git history since the latest tag.
---

# Generate Changelog Skill

Run this skill or command `/generate-changelog` to analyze git history and produce a standardized `CHANGELOG.md` adhering to the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standard.

## Instructions

1. Identify the latest git tag using `git describe --tags --abbrev=0`.
2. Retrieve all commit messages between that tag and `HEAD`.
3. Auto-categorize commits into:
   - `Added`: Features, additions (`feat:`, `feature:`, `add:`)
   - `Fixed`: Bug fixes, patches (`fix:`, `patch:`)
   - `Changed`: Modifications, refactoring (`refactor:`, `perf:`, `chore:`, `update:`)
   - `Removed`: Removals and deprecations (`remove:`, `deprecate:`)
4. Prepend the categorized entry with the current date into `CHANGELOG.md`.

## Execution

```bash
bash skills/generate-changelog/changelog.sh
```
or
```bash
python3 skills/generate-changelog/generate_changelog.py
```
