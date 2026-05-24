# Generate Changelog

Generate a structured `CHANGELOG.md` from git history since the last tag.

## Setup and usage

1. Copy `changelog.sh` into any git repository and make it executable:
   ```bash
   chmod +x changelog.sh
   ```
2. Run it from the repository root:
   ```bash
   ./changelog.sh
   ```
3. Review the generated `CHANGELOG.md` and commit it.

## Optional usage

Generate for an explicit range:

```bash
./changelog.sh v1.2.0..HEAD
```

Write to a custom file:

```bash
CHANGELOG_FILE=RELEASE-NOTES.md ./changelog.sh
```

## Categorization

The script reads non-merge commit subjects from `git log`, defaulting to commits
since the latest git tag. If no tag exists, it uses the repository history.

It groups commits into:

- `Added`: `feat:`, `feature:`, `add`, `created`, `introduced`
- `Fixed`: `fix:`, `bugfix:`, `fixed`, `resolved`, `patched`
- `Changed`: `change:`, `refactor:`, `perf:`, `chore:`, `docs:`, `test:`, `ci:`, `updated`, `improved`, `renamed`
- `Removed`: `remove:`, `delete:`, `drop`, `removed`, `deleted`

Empty categories are rendered as `- None` so the generated file is always a
properly structured changelog.

## Sample output

A real sample generated from this repository is included at:

```text
samples/generated-changelog.md
```
