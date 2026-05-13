# Generate Changelog

Generate a structured `CHANGELOG.md` from a repository's git history.

## Setup in 3 steps

1. Copy this directory into your repository.
2. Run `bash generate-changelog/changelog.sh` from the repository root.
3. Review and commit the generated `CHANGELOG.md`.

## What it does

- Finds the latest git tag and reads commits from that tag to `HEAD`.
- Falls back to all commits when the repository has no tags.
- Skips merge commits.
- Categorizes entries into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a properly formatted `CHANGELOG.md`.

## Category rules

- `Added`: `feat:`, `add:`, `implement:`, or subjects containing add/new/introduce/implement.
- `Fixed`: `fix:`, `bug:`, `hotfix:`, or subjects containing fix/bug/resolve.
- `Removed`: `remove:`, `delete:`, `deprecate:`, or matching keywords.
- `Changed`: everything else, including docs, refactors, chores, and performance work.

## Example

```bash
bash generate-changelog/changelog.sh
# Wrote CHANGELOG.md
```

To preview without overwriting the project changelog:

```bash
CHANGELOG_OUTPUT=/tmp/CHANGELOG.preview.md bash generate-changelog/changelog.sh
```

See `SAMPLE_CHANGELOG.md` for output generated from a real git repository.
