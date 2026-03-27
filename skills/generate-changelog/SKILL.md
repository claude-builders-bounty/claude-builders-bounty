---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag.
---

# Generate CHANGELOG

Use this skill when the user asks to generate or update a `CHANGELOG.md` from git history.

## Command

```bash
bash skills/generate-changelog/changelog.sh
```

## What it does
- Finds the most recent git tag
- Reads commits since that tag
- Categorizes commit subjects into:
  - Added
  - Fixed
  - Changed
  - Removed
- Writes a formatted `CHANGELOG.md`

## Categorization rules
- **Added**: `feat`, `add`, `create`, `implement`
- **Fixed**: `fix`, `bug`, `patch`, `hotfix`
- **Changed**: `refactor`, `update`, `change`, `perf`, `docs`, `style`, `chore`
- **Removed**: `remove`, `delete`, `drop`, `deprecate`
- Anything unmatched goes to **Changed**

## Notes
- If there is no tag yet, use the full history.
- The generated changelog is a starting point; review before publishing.
