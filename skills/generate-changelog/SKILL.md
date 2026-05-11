---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the last tag.
---

# Generate Changelog

Use this skill when a project needs a release-ready `CHANGELOG.md` generated from
recent git history.

## Workflow

1. Run `bash changelog.sh --repo . --output CHANGELOG.md` from the project root.
2. Review the generated `Added`, `Fixed`, `Changed`, and `Removed` sections.
3. Edit only when a commit subject needs human release-note wording.

## Categorization

- `feat`, `feature`, `add`, `added` -> `Added`
- `fix`, `bugfix`, `patch` -> `Fixed`
- `remove`, `delete`, `drop` -> `Removed`
- docs, chores, refactors, tests, CI, builds, performance, updates, and unknown
  prefixes -> `Changed`

## Notes

The generator uses the most recent git tag as its lower bound. If the repository
has no tags, it writes a changelog from the first commit.

Relative output paths are resolved inside the target repository.
