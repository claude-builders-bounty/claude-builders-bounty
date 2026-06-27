# Generate Changelog

Generate a structured `CHANGELOG.md` from git history.

## Usage

Run this command from the root of any git repository:

```bash
bash generate-changelog/changelog.sh
```

To write to a different file:

```bash
bash generate-changelog/changelog.sh RELEASE_NOTES.md
```

## What it does

- Fetches tags when a remote is configured.
- Uses commits since the latest git tag, or the full repository history when no tag exists.
- Ignores merge commits.
- Groups commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown changelog with short commit hashes for traceability.

## Categorization rules

- `feat:`, `add:`, `new:`, `implement:`, `initial:`, `create:` → `Added`
- `fix:`, `bug:`, `bugfix:`, `repair:`, `resolve:`, `hotfix:` → `Fixed`
- `remove:`, `delete:`, `deprecate:`, `drop:` → `Removed`
- Everything else → `Changed`
