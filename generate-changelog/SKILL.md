---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when a user asks for `/generate-changelog`, release notes, or a
structured changelog derived from git history.

## Workflow

1. Confirm the current directory is the git repository that should receive the
   changelog.
2. Run:

   ```bash
   bash generate-changelog/changelog.sh
   ```

3. Review `CHANGELOG.md` before committing it.

## Rules

- Use the latest git tag as the release boundary.
- If no tags exist, summarize the full repository history.
- Exclude merge commits.
- Keep categories in this order: `Added`, `Fixed`, `Changed`, `Removed`.
- Preserve original commit subjects so readers can trace entries back to git.
- Include short commit hashes by default.

## Category Guidance

- `Added`: features, new files, new commands, first implementation work.
- `Fixed`: corrections, regressions, broken behavior, repair work.
- `Changed`: documentation, refactors, dependency updates, behavior improvements,
  maintenance, CI, tests, style, and build changes.
- `Removed`: removals, deletions, deprecations, reverts, and dropped support.

If a commit could fit multiple categories, choose the category with the clearest
user-facing effect. For example, `fix(parser): support empty input` belongs in
`Fixed` because it corrects behavior, even though it also adds coverage.
