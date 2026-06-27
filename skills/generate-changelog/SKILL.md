---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the last tag.
---

# Generate Changelog

Use this when a repository needs a quick release changelog from git history.

## Procedure

1. From the repository root, run `bash changelog.sh`.
2. Review the generated `CHANGELOG.md` sections: Added, Fixed, Changed, Removed.
3. Edit wording only if a commit subject is unclear.

## Notes

The script uses the latest git tag as the start point. If the repository has no tags, it uses the full history.
