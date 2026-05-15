---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag, grouped into Added, Fixed, Changed, and Removed.
---

# Generate Changelog

Use this skill when a user asks for a changelog, release notes, or a summary of repository changes from git commits.

## Steps

1. Run `bash changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md` for wording and category accuracy.
3. Mention the commit range used: latest tag to `HEAD`, or all history if no tag exists.

## Behavior

The script:

- detects the latest git tag and reads commits from that tag to `HEAD`,
- falls back to all history when no tag exists,
- groups commits into `Added`, `Fixed`, `Changed`, and `Removed`,
- writes a Markdown `CHANGELOG.md`.

## Optional Arguments

```bash
bash changelog.sh --repo /path/to/repo --output /tmp/CHANGELOG.md
bash changelog.sh --range v1.0.0..HEAD
```
