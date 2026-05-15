---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history when the user asks for /generate-changelog, release notes, or a changelog since the latest git tag.
---

# Generate Changelog

Use this skill to create or update `CHANGELOG.md` from a repository's git history.

## Workflow

1. Run the bundled script from the target repository root:

   ```bash
   bash scripts/changelog.sh
   ```

2. Review the generated categories:

   - `Added`: `feat`, `add`, `create`, `implement`, `introduce`
   - `Fixed`: `fix`, `bugfix`, `resolve`, `repair`
   - `Changed`: `change`, `update`, `improve`, `refactor`, `perf`, `docs`, `test`, `build`, `ci`, `chore`, `style`
   - `Removed`: `remove`, `delete`, `drop`, `deprecate`

3. If needed, rerun with options:

   ```bash
   bash scripts/changelog.sh --version v1.2.0 --from v1.1.0 --to HEAD --output CHANGELOG.md
   ```

## Notes

- With no `--from`, the script uses the most recent git tag reachable from `HEAD`.
- If the repository has no tags, it uses the full history.
- Existing `CHANGELOG.md` files are preserved by prepending the new section under the title.
