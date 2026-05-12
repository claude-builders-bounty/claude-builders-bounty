---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

When asked to generate a changelog:

1. Run `bash generate-changelog/changelog.sh`.
2. Open `CHANGELOG.md` and verify the categories are sensible.
3. Mention the detected tag range and any commits that landed in `Changed` because they did not match a more specific category.

Do not invent release notes. Use only commit subjects from git history.

