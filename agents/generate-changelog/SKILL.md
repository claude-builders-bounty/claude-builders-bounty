---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history.
---

# Generate changelog

Use this skill when a user asks for a changelog from git history.

## Command

Run:

```bash
bash changelog.sh
```

The script finds the latest git tag, reads commits after that tag, and writes a `CHANGELOG.md` with these sections:

- Added
- Fixed
- Changed
- Removed

If no git tag exists, it uses the whole history.

