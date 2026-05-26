---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag
---

# Generate Changelog

Use this skill when a project needs a release changelog generated from local git history.

## Command

Run:

```bash
bash changelog.sh
```

Optional flags:

```bash
bash changelog.sh --since v1.2.0 --output CHANGELOG.md
```

## Behavior

The script reads commits since the latest git tag, categorizes them into `Added`, `Fixed`, `Changed`, and `Removed`, and writes a Markdown changelog. Conventional commit prefixes are preferred when present:

- `feat:` -> `Added`
- `fix:` -> `Fixed`
- `refactor:`, `perf:`, `docs:`, `style:`, `test:`, `chore:` -> `Changed`
- `remove:`, `delete:`, `drop:`, `deprecate:` -> `Removed`

If no tag exists, it uses all commits in the repository.

## Verification

After generation, inspect `CHANGELOG.md` and confirm each section is present. Empty sections are shown as `- None`.
