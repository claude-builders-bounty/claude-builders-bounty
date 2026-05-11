---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, grouped into Added, Fixed, Changed, and Removed sections using commits since the latest git tag.
---

# Generate Changelog

Use this skill when a user asks for a `CHANGELOG.md` from repository git history.

## Workflow

1. Run `bash generate-changelog/changelog.sh` from the repository root.
2. Review `CHANGELOG.md` for project-specific wording before committing.
3. If the project uses non-standard commit messages, pass `--since <tag>` or edit section placement after generation.

## Behavior

- Fetches tags from `origin` when a remote exists.
- Uses the latest reachable git tag as the default starting point.
- Falls back to the full git history when the repository has no tags.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep a Changelog-style `CHANGELOG.md`.

## Options

```bash
bash generate-changelog/changelog.sh --since v1.2.3 --version 1.3.0 --output CHANGELOG.md
```

Use `--no-fetch` when running offline or when the local tag state is already correct.
