---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog` or wants a changelog generated from the current repository's git history.

## Command

Run the bundled script from the repository root:

```bash
bash changelog.sh
```

To write to a custom path:

```bash
bash changelog.sh RELEASE_NOTES.md
```

## Behavior

The script:

- finds the latest git tag and reads commits from that tag to `HEAD`
- falls back to all history when the repository has no tags
- categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`
- writes a formatted changelog file

