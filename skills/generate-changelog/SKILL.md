---
name: generate-changelog
description: "Generates a structured, standardized CHANGELOG.md from git commit history since the latest tag."
version: 1.0.0
author: zarya8096-max
license: MIT
---

# Generate Changelog Skill

Automatically inspects repository history since the latest git tag, parses commit conventions, categorizes entries into `Added`, `Fixed`, `Changed`, and `Removed`, and formats `CHANGELOG.md` according to the [Keep a Changelog](https://keepachangelog.com) standard.

## Trigger Command

Run in any repository terminal:
```bash
/generate-changelog
```
Or directly via shell:
```bash
bash skills/generate-changelog/changelog.sh [version]
```

## Behavior & Output Rules

1. Detects git tags automatically via `git describe --tags --abbrev=0`.
2. Gathers commit ranges (`<latest-tag>..HEAD`).
3. Categorizes conventional commits:
   - `feat`, `add`, `new` -> **Added**
   - `fix`, `bug`, `resolve`, `patch` -> **Fixed**
   - `refactor`, `perf`, `chore`, `update` -> **Changed**
   - `remove`, `delete`, `deprecate` -> **Removed**
4. Prepends the formatted version block to `CHANGELOG.md` preserving previous history.
