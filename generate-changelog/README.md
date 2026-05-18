# Generate Changelog

Create a structured `CHANGELOG.md` from a repository's git history.

## Setup

1. Copy this package into the target git repository.
2. Run `bash changelog.sh` from the repository root.
3. Open `CHANGELOG.md` and review the generated release notes.

## What It Does

- Fetches tags and finds the latest git tag.
- Reads non-merge commits since that tag.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a formatted `CHANGELOG.md` at the repository root.

## Options

```bash
bash changelog.sh --output docs/CHANGELOG.md
bash changelog.sh --no-fetch
```

## Category Rules

- `Added`: commits beginning with `feat:`, `feature:`, `add:`, `added:`, or `new:`
- `Fixed`: commits beginning with `fix:`, `bug:`, `bugfix:`, `resolve:`, `resolved:`, or `patch:`
- `Removed`: commits beginning with `remove:`, `removed:`, `delete:`, `deleted:`, `drop:`, `dropped:`, `deprecate:`, or `deprecated:`
- `Changed`: all other non-merge commits

See `examples/sample-output.md` for output produced during testing on a real GitHub repository.
