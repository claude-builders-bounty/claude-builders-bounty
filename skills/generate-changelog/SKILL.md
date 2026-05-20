---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when a project needs a quick, structured changelog from commit history.

## Command

Run from the root of a git repository:

```bash
bash skills/generate-changelog/changelog.sh
```

To write to a different path:

```bash
bash skills/generate-changelog/changelog.sh RELEASE_NOTES.md
```

## Behavior

The generator:

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- Uses commits since that tag, or all commits if the repository has no tags.
- Skips merge commits.
- Groups commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a complete Markdown changelog to `CHANGELOG.md` by default.

## Categorization Rules

- `Added`: `feat:`, `feature:`, or subjects containing add/added/new/introduced.
- `Fixed`: `fix:`, `bugfix:`, or subjects containing fix/fixed/bug/patched/resolved.
- `Removed`: subjects containing remove/delete/drop/deprecate variants.
- `Changed`: everything else.

After generating the changelog, review the output once and manually adjust any commit whose wording does not make the intent obvious.
