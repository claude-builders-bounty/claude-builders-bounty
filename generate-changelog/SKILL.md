---
title: Generate Changelog
command: generate-changelog
description: Auto-generate a structured CHANGELOG.md from git history since the last tag
tags:
  - git
  - changelog
  - documentation
---

# Generate Changelog

## Usage

```bash
bash generate-changelog/changelog.sh
```

## What it does
1. Detects the latest git tag (or uses all commits if no tags exist)
2. Reads commits since that tag
3. Auto-categorizes each commit into Added / Fixed / Changed / Removed / Other
4. Writes a formatted `CHANGELOG.md`

## Requirements
- `git` CLI
- Bash 4+
- Run from the repo root
