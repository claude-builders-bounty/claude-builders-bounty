---
name: generate-changelog
description: Generate or refresh a structured CHANGELOG.md from git history since the latest tag, categorizing commits into Added, Fixed, Changed, and Removed.
---

# Generate Changelog

Use this skill when a project needs a `CHANGELOG.md` generated from git commit history.

## Workflow

1. Run the bundled script from the repository root:

   ```bash
   bash changelog.sh
   ```

2. Review `CHANGELOG.md` and confirm the range shown under `Unreleased` matches the latest git tag.
3. If the repository has no tags, the script uses all reachable commits and says so in the output.

## Categorization

- `Added`: `feat`, `add`, `implement`, `introduce`.
- `Fixed`: `fix`, `bug`, `repair`, `resolve`.
- `Removed`: `remove`, `delete`, `drop`, `deprecate`, breaking changes.
- `Changed`: all remaining commits.

Do not invent release notes. Only summarize commit subjects returned by git.
