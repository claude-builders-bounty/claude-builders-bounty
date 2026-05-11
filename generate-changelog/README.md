# Generate Changelog

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup in 3 steps

1. Copy the `generate-changelog/` directory into any git repository.
2. Run `bash generate-changelog/changelog.sh`.
3. Review the generated `CHANGELOG.md` before committing it.

## Usage

```bash
bash generate-changelog/changelog.sh
```

Optional flags:

```bash
# Inspect a different repository and print the changelog
bash generate-changelog/changelog.sh --repo /path/to/repo --dry-run

# Write to a custom path
bash generate-changelog/changelog.sh --output docs/CHANGELOG.md
```

## Behavior

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Reads commits from `latest-tag..HEAD`.
- Falls back to full history when the repository has no tags.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown `CHANGELOG.md`.

## Categorization

| Category | Commit patterns |
| --- | --- |
| Added | `feat:`, `feature:`, `add:`, `add ...`, `implement ...` |
| Fixed | `fix:`, `bugfix:`, subjects containing `fix`, `bug`, `repair`, or `resolve` |
| Removed | `remove:`, `delete:`, subjects containing `remove`, `delete`, `drop`, or `deprecate` |
| Changed | everything else |

## Sample Output

See `samples/claude-builders-bounty-changelog.md` for a real generated sample.
