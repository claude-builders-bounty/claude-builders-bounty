---
name: generate-changelog
description: Generate a structured CHANGELOG.md from commits since the latest git tag.
---

# Generate Changelog

Use this skill when a project needs a quick release changelog from git history.

## Steps

1. Run `bash changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md` sections: `Added`, `Fixed`, `Changed`, and `Removed`.
3. Edit wording only when a commit subject needs human cleanup before release.

## Behavior

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- Uses all commits when a repository has no tags.
- Categorizes conventional commits first, then falls back to keyword matching.
- Writes a Keep-a-Changelog-style markdown file.
