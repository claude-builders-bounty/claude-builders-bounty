---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Run this skill when the user asks to create or refresh a changelog from commit history.

## Steps

1. From the target repository root, run:

```bash
bash generate-changelog/changelog.sh
```

2. Inspect `CHANGELOG.md`.
3. Ask for release-specific wording only if the generated categories need editorial cleanup.
