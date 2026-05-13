# Generate Changelog

Create a structured `CHANGELOG.md` from git history.

## Setup

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
```

To write to another file:

```bash
bash changelog.sh docs/SAMPLE_CHANGELOG.md
```

The script reads commits since the latest git tag. If the repository has no tags, it uses the full repository history. Merge commits are skipped so the changelog reflects authored changes.

## Categories

- `Added`: `feat:`, `add:`, `create:`, `implement:`, and similar subjects.
- `Fixed`: `fix:`, `bug:`, `hotfix:`, and similar subjects.
- `Changed`: uncategorized updates, refactors, docs, chore, and maintenance commits.
- `Removed`: `remove:`, `delete:`, `drop:`, `deprecate:`, and similar subjects.
