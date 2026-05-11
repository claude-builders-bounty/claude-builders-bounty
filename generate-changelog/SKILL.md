---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when the user asks to generate or refresh a `CHANGELOG.md` from git history.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run:

```bash
bash generate-changelog/changelog.sh
```

3. Review `CHANGELOG.md` and adjust wording only if the generated commit summaries need human polish.

## Notes

- The script uses the latest git tag as the lower bound.
- If the repository has no tags, it uses the full git history.
- Categories are limited to `Added`, `Fixed`, `Changed`, and `Removed`.
