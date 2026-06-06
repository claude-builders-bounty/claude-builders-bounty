---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Use when Codex needs to create, refresh, or preview release notes from commits since the last tag, with Added, Fixed, Changed, and Removed sections.
---

# Generate Changelog

Use this skill to produce a concise `CHANGELOG.md` from commit history.

## Workflow

1. Inspect the repository's existing release notes or changelog style if one exists.
2. Run the bundled script:
   ```bash
   bash changelog.sh --output CHANGELOG.md
   ```
3. Review the generated sections, merge duplicate bullets, and keep only user-facing changes unless the project intentionally tracks internal maintenance.

## Remote Repositories

When `git` is unavailable or the repo is remote-only, use GitHub API mode:

```bash
bash changelog.sh --repo owner/name --dry-run
```

The script reads commits on the default branch until the most recent tag. If no tag exists, it uses recent commits from the default branch.

## Categorization Rules

- `feat`, `feature`, `add`, `create`, `implement`, `introduce`, `support` -> `Added`
- `fix`, `bugfix`, `hotfix`, `resolve`, `patch` -> `Fixed`
- `remove`, `delete`, `drop`, `deprecate` -> `Removed`
- Everything else -> `Changed`

Prefer editing the final changelog for clarity over preserving raw commit wording exactly.
