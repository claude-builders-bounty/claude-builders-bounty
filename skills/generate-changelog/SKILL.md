---
name: generate-changelog
description: Generate a structured CHANGELOG.md from the current repository's git history.
---

# Generate Changelog

Use this skill when the user asks to generate, refresh, or preview a changelog
from git history.

## Command

Run the repository script from the project root:

```bash
bash changelog.sh
```

To preview without writing:

```bash
bash changelog.sh --dry-run
```

## Behavior

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- Reads non-merge commits since that tag. If no tag exists, it uses all history.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep a Changelog-style `CHANGELOG.md`.

## Notes

Use `--since <ref>` to override the detected tag and `--output <path>` to choose
a custom destination.
