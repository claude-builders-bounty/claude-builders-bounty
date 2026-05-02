---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the last tag.
---

# Generate Changelog

Use this skill when a user asks to generate or refresh a `CHANGELOG.md` from a repository's git history.

## Command

Run this from the target repository root:

```bash
bash changelog.sh
```

Optional flags:

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md
```

## Behavior

The script:

1. Detects the latest git tag with `git describe --tags --abbrev=0`.
2. Fetches non-merge commits from `LAST_TAG..HEAD`.
3. Categorizes commits into:
   - `Added`
   - `Fixed`
   - `Changed`
   - `Removed`
4. Writes a formatted `CHANGELOG.md`.

## Categorization rules

- `feat:` / `feature:` / add/create/implement/support → `Added`
- `fix:` / bug/patch/resolve/correct → `Fixed`
- remove/delete/drop/deprecate → `Removed`
- docs/chore/refactor/ci/build/test/perf/style/update/improve → `Changed`

If no tag exists, the script uses all commits in the repository.
