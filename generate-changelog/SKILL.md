---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history for a repository, grouping commits into Added, Fixed, Changed, and Removed sections.
---

# Generate Changelog

Use this skill when a user asks to create or update a `CHANGELOG.md` from a
repository's git history.

## Workflow

1. Inspect the repository's tags with `git tag --sort=-creatordate`.
2. Generate changelog entries from commits since the latest tag. If there are no
   tags, use all commits.
3. Group entries by commit intent:
   - `feat`, `feature`, `add`: Added
   - `fix`, `bug`, `patch`: Fixed
   - `remove`, `delete`, `drop`, `deprecate`: Removed
   - anything else: Changed
4. Preserve short commit hashes and author names when useful for review.
5. Write the result to `CHANGELOG.md`.

## Scripted Path

Prefer the bundled script for repeatable output:

```bash
python generate-changelog/scripts/generate_changelog.py --output CHANGELOG.md
```

Useful options:

```bash
python generate-changelog/scripts/generate_changelog.py --from v1.0.0 --output CHANGELOG.md
python generate-changelog/scripts/generate_changelog.py --repo /path/to/repo --output /path/to/repo/CHANGELOG.md
```

Review the generated file before final delivery and remove noisy merge commits
only when they do not add useful release context.
