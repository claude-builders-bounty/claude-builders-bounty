---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest git tag.
---

# Generate Changelog

Use this skill when a project needs a `CHANGELOG.md` generated from git commits.

## What It Does

- Finds the latest reachable git tag and reads commits after that tag.
- Falls back to the full git history when the repository has no tags.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown changelog that includes commit references.

## Command

From the repository root:

```bash
bash changelog.sh
```

To write to a custom path or inspect another repository:

```bash
bash changelog.sh docs/CHANGELOG.md /path/to/repo
```

## Categorization

- `Added`: `feat`, `feature`, `add`, `new`
- `Fixed`: `fix`, `bugfix`, `patch`, `hotfix`
- `Removed`: `remove`, `delete`, `drop`
- `Changed`: `change`, `refactor`, `perf`, `docs`, `test`, `build`, `ci`, `chore`, and uncategorized commits
