---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a git repository's commit history. Use when the user asks for /generate-changelog, a release changelog, or a changelog grouped by Added, Fixed, Changed, and Removed since the latest git tag.
---

# Generate Changelog

Use `changelog.sh` from the repository root to generate `CHANGELOG.md` from commits since the latest reachable git tag.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run `bash changelog.sh` to fetch tags, read commits since the latest tag, categorize changes, and write `CHANGELOG.md`.
3. Review the generated `CHANGELOG.md` for project-specific wording before committing it.

## Options

- Use `bash changelog.sh --stdout` to preview without writing a file.
- Use `bash changelog.sh --since <tag-or-ref>` to override the starting ref.
- Use `bash changelog.sh --no-fetch` when working offline or avoiding network access.

## Categories

- `Added`: `feat`, `feature`, `add`, `implement`, `introduce`, `support`, and similar subjects.
- `Fixed`: `fix`, `bugfix`, `hotfix`, `resolve`, and bug/error/crash wording.
- `Removed`: `remove`, `delete`, `drop`, `deprecate`, and `revert`.
- `Changed`: refactors, docs, tests, build/CI, chores, updates, and fallback entries.
