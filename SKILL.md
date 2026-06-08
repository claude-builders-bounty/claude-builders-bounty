---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last git tag.
---

# Generate Changelog Skill

Use this skill when the user asks to generate, refresh, or maintain a `CHANGELOG.md` from git history.

## Command

Run this from the project root:

```bash
bash changelog.sh
```

## What it does

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Reads commits from that tag to `HEAD`.
- If the repository has no tag, reads all non-merge commits.
- Categorizes commits into:
  - `Added`
  - `Fixed`
  - `Changed`
  - `Removed`
- Writes the result to `CHANGELOG.md`.

## Notes

The categorization is deterministic and based on conventional commit prefixes plus simple keyword heuristics, so it runs locally without API keys or network access.
