---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when the user asks to create or refresh a `CHANGELOG.md` from a git repository.

## Command

Run this from the repository root:

```bash
bash changelog.sh
```

Optional flags:

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md
bash changelog.sh --since v1.2.3 --output RELEASE_NOTES.md
```

## Behavior

- Reads commits after the latest reachable git tag.
- If the repository has no tags, reads the full commit history.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a complete Markdown changelog with the current date and source range.
- Keeps commit subjects concise and links each entry to its short SHA.

## Review Checklist

1. Run the command from a real git repository.
2. Inspect the generated categories for obvious misclassification.
3. Commit the generated `CHANGELOG.md` only when it matches the release scope.
