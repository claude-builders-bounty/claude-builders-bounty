# Generate a structured changelog

`changelog.sh` generates a `CHANGELOG.md` from git history since the latest tag. If the repository has no tags, it uses the full commit history.

## Setup in 3 steps

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh` to write `CHANGELOG.md`, or `bash changelog.sh docs/CHANGELOG.md` to choose an output path.
3. Review the generated `Added`, `Fixed`, `Changed`, and `Removed` sections before publishing.

## Categorization rules

The script reads commit subjects and maps common prefixes/phrases:

- `Added`: `feat:`, `feature:`, `add:`, `new:`, or subjects that contain add/adds phrasing
- `Fixed`: `fix:`, `bugfix:`, `bug:`, or subjects that contain fix/fixes/fixed phrasing
- `Removed`: `remove:`, `delete:`, `drop:`, or related past-tense prefixes
- `Changed`: `change:`, `update:`, `refactor:`, `perf:`, `docs:`, `test:`, `chore:`, and uncategorized commits

## Real-repository smoke test

Test repository: this bounty repository clone.

Command:

```bash
bash changelog.sh /tmp/sample-CHANGELOG.md
```

Sample output:

```text
# Changelog

Generated on 2026-05-11 (from repository history).

## Added

- feat: initial README with bounty board (1aeae2a)

## Fixed

- No changes.

## Changed

- Initial commit (a80a580)

## Removed

- No changes.
```
