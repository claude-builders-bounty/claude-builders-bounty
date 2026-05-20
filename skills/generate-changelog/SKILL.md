---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Run this from a git repo root:

```bash
bash changelog.sh
```

The script finds the latest git tag, reads non-merge commit subjects since that tag, categorizes them into `Added`, `Fixed`, `Changed`, and `Removed`, then writes `CHANGELOG.md`.
