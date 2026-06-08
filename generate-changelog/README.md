# Generate Changelog

`changelog.sh` creates a structured `CHANGELOG.md` from git commits since the most recent tag. If the repository has no tags, it uses the full history.

## Setup

1. Copy `changelog.sh` to the root of a git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md` before committing it.

## Categorization

The script groups commit subjects into:

- `Added`: `feat:`, `add:`, `create:`, `implement:`, `introduce:`
- `Fixed`: `fix:`, `bug:`, `bugfix:`, `patch:`, `repair:`, `resolve:`
- `Changed`: `change:`, `update:`, `refactor:`, `docs:`, `test:`, `ci:`, `build:`, `style:`, `chore:`
- `Removed`: `remove:`, `delete:`, `drop:`, `deprecate:`

It also falls back to keyword matching for non-conventional commit subjects.

## Examples

Generate the default changelog:

```bash
bash changelog.sh
```

Write to a custom path:

```bash
bash changelog.sh docs/CHANGELOG.md
```

See `SAMPLE_OUTPUT.md` for output generated from this repository's `main` branch before this bounty implementation was added.
