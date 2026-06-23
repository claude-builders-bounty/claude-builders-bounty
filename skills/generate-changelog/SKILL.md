---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when a repository needs a release-ready `CHANGELOG.md` generated from recent git commits.

## Command

Run the bundled script from the repository root:

```bash
bash skills/generate-changelog/changelog.sh
```

The script:

1. Detects the latest reachable git tag and collects commits after that tag.
2. Falls back to all commits when the repository has no tags.
3. Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
4. Writes a Markdown `CHANGELOG.md` with commit hashes and dates.

## Categorization

- `Added`: `feat`, `feature`, `add`, `create`, `introduce`
- `Fixed`: `fix`, `bugfix`, `repair`, `resolve`, `patch`
- `Removed`: `remove`, `delete`, `drop`, `deprecate`
- `Changed`: all other commits, including `refactor`, `docs`, `chore`, `style`, `test`, `build`, and `ci`

## Usage Notes

- Run from inside a git repository.
- Re-run the command whenever new commits land before a release.
- Review the generated file before publishing because commit messages may need editorial cleanup.
