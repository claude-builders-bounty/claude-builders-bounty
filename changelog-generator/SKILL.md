---
name: generate-changelog
description: Auto-generate a structured CHANGELOG.md from git history since the last tag.
version: 1.0.0
author: 1vvvflow
---

# Generate Changelog

Generates a structured `CHANGELOG.md` from git commits since the last tag.

## Usage

Run via Hermes slash command: `/generate-changelog`
Or manually: `bash changelog.sh`

## How It Works

1. Finds the most recent git tag
2. Collects all commits since that tag
3. Categorizes commits into: Added, Fixed, Changed, Removed
4. Outputs to `CHANGELOG.md` in Keep a Changelog format

## Script

The script is located at `changelog.sh`. To run it:

```bash
bash changelog.sh [--output CHANGELOG.md] [--since <tag>]
```
