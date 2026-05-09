---
name: generate-changelog
description: Generate a structured CHANGELOG.md from the current git repository history.
---

# Generate Changelog

Use this skill when a project needs a quick `CHANGELOG.md` generated from git commits since the latest tag.

## Command

```bash
bash changelog.sh
```

The script:

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Falls back to all repository history when no tag exists.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown `CHANGELOG.md` at the repository root.

## Notes

- Conventional commits produce the cleanest categories.
- Non-conventional commits are kept under `Changed` so no work is silently dropped.
- GitHub commit links are included when `remote.origin.url` points to GitHub.
