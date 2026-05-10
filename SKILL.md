---
name: generate-changelog
description: Generate a structured CHANGELOG.md from commits since the last git tag.
---

# Generate changelog

Use this skill when a user asks Claude Code to create or refresh a `CHANGELOG.md` from git history.

## Command

Run this from the root of the target repository:

```bash
bash changelog.sh
```

Optional output path:

```bash
bash changelog.sh docs/CHANGELOG.md
```

## What it does

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Reads non-merge commits from the latest tag to `HEAD`.
- If the project has no tags, reads the full history.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown changelog with commit SHA, author, and date.

## Category rules

- `Added`: `feat:`, `feature:`, `add:`, `added:`, `implement`, `introduce`
- `Fixed`: `fix:`, `bugfix:`, `hotfix:`, `bug`, `repair`
- `Removed`: `remove:`, `delete:`, `drop:`, `deprecat`
- `Changed`: anything else

## Verification

After generation, inspect the output and compare against the raw commit list:

```bash
git log $(git describe --tags --abbrev=0 2>/dev/null)..HEAD --no-merges --oneline
bash changelog.sh
sed -n '1,120p' CHANGELOG.md
```

For repositories with no tags, omit the range check and compare against:

```bash
git log --no-merges --oneline
```
