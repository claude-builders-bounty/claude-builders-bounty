---
name: structured-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag.
---

# Structured Changelog Skill

Use this skill when you need to convert git history into a release-friendly `CHANGELOG.md`.

## What it does

- Reads commits since the latest git tag
- Categorizes them into:
  - `Added`
  - `Fixed`
  - `Changed`
  - `Removed`
- Writes a formatted `CHANGELOG.md`

## Usage

```bash
bash changelog.sh
```

Optional arguments:

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md --version Unreleased
```
