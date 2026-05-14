---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history since the latest tag.
---

# Generate Changelog

Use this skill when a user wants to create or refresh a project's `CHANGELOG.md` from Git history.

## Command

Run from the root of any Git repository:

```bash
bash changelog.sh
```

Optionally pass a custom output path:

```bash
bash changelog.sh docs/CHANGELOG.md
```

## What it does

1. Finds the latest Git tag with `git describe --tags --abbrev=0`.
2. Reads non-merge commits from that tag to `HEAD`; if no tag exists, it uses the full history.
3. Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
4. Writes a Markdown `CHANGELOG.md` using a Keep a Changelog-style structure.

## Categorization rules

- `Added`: `feat:`, `add`, `added`, `implement`, `introduce`
- `Fixed`: `fix:`, `bug`, `resolve`, `resolved`
- `Removed`: `remove`, `removed`, `delete`, `deleted`, `deprecate`
- `Changed`: everything else

## Verification

Run the regression test from this repository to verify tag-range handling and all four categories:

```bash
bash tests/test-changelog.sh
```

## Notes

- The script attempts to fetch tags first so it works better in CI and shallow clones.
- Merge commits are skipped to keep the generated changelog focused on user-visible changes.
