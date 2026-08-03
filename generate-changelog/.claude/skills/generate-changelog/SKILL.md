---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Use when the user asks for a changelog, release notes, or runs /generate-changelog.
---

# Generate Changelog

Create or refresh `CHANGELOG.md` from commits since the latest git tag.

## Steps

1. Confirm you are inside a git repository.
2. Run the generator from the repo that contains this skill:

```bash
bash generate-changelog/changelog.sh CHANGELOG.md
```

If this skill was copied into another project, run the bundled script path instead, or copy `changelog.sh` next to the project root and run:

```bash
bash changelog.sh CHANGELOG.md
```

3. Review the generated `CHANGELOG.md`.
4. Briefly summarize what landed in **Added / Fixed / Changed / Removed**.

## Categorization rules

| Section | Commit signals |
|---------|----------------|
| Added | `feat:`, `feature:`, `add`, `implement` |
| Fixed | `fix:`, `bugfix`, `hotfix` |
| Changed | `update`, `refactor`, `perf`, `chore`, `docs`, `improve`, `change` |
| Removed | `remove`, `delete`, `drop`, `revert` |

Uncategorized commits are listed under **Changed** so nothing is dropped.

## Notes

- Range is `last-tag..HEAD`. If there are no tags, the full history is used.
- Prefer conventional commits for clean sections.
- Do not invent commit messages; only use git history.
