---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a repository's git history.
---

# Generate Changelog

Use this skill when a project needs a changelog section generated from recent commits.

## Command

Run:

```bash
python skills/generate-changelog/changelog.py --repo .
```

## What It Does

- Finds commits since the latest git tag, or since a revision supplied with `--since`.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a markdown `CHANGELOG.md` that is ready for review.

## Good Review Checklist

- Confirm the latest tag is the intended release boundary.
- Rewrite terse commit messages into user-facing wording if needed.
- Remove internal-only commits that should not appear in release notes.
