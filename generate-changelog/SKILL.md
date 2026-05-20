---
name: generate-changelog
description: Generate or update a structured CHANGELOG.md from git history. Use when the user asks for /generate-changelog, changelog generation, release notes from commits since the last tag, or categorized Added/Fixed/Changed/Removed sections.
---

# Generate Changelog

## Workflow

1. Run `scripts/changelog.sh` from the target git repository, or use the root `changelog.sh` wrapper from this skill.
2. Review the generated `CHANGELOG.md` for project-specific wording before committing it.
3. If the repository uses non-conventional commit messages, keep the generated categorization but adjust ambiguous items manually.

## Script

Use the bundled Bash script for deterministic output:

```bash
bash /path/to/generate-changelog/changelog.sh
```

The script:

- Finds the latest reachable git tag with `git describe --tags --abbrev=0`.
- Reads commits in `<last-tag>..HEAD`; if no tag exists, it uses all commits.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Prepends a new `Unreleased - YYYY-MM-DD` section to `CHANGELOG.md`.

## Categorization

- `Added`: `feat`, `add`, `create`, `implement`, `introduce`.
- `Fixed`: `fix`, `bug`, `repair`, `resolve`.
- `Removed`: `remove`, `delete`, `drop`, `deprecate`.
- `Changed`: everything else, including `chore`, `docs`, `refactor`, `perf`, `test`, `build`, and `ci`.

Prefer preserving the script output exactly for auditability, then make small wording edits only when needed.
