---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, grouping commits since the last tag into Added, Fixed, Changed, and Removed sections. Use when the user asks for /generate-changelog, release notes, or a changelog from commits.
---

# Generate Changelog

Use this skill when a project needs a `CHANGELOG.md` generated from git history.

## Workflow

1. Run the bundled script from the repository root:

   ```bash
   bash changelog.sh
   ```

2. Review the generated `CHANGELOG.md` for wording that should be clearer to users.
3. If the user wants a custom range, rerun with explicit refs:

   ```bash
   bash changelog.sh --from-ref v1.2.0 --to-ref HEAD
   ```

## Behavior

- Finds commits since the latest reachable git tag by default.
- Groups entries into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a formatted `CHANGELOG.md`.
- Uses only Python standard-library modules and the local `git` executable.
- Supports `--stdout`, `--output`, `--repo`, `--from-ref`, `--to-ref`, and `--include-merges`.

## Categorization

- `feat`, `add`, `create`, `implement` -> `Added`
- `fix`, `bugfix`, `hotfix`, `repair`, `resolve` -> `Fixed`
- `remove`, `delete`, `drop`, `deprecate` -> `Removed`
- Everything else -> `Changed`
