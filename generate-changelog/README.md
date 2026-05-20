# Generate Changelog

Generate a structured `CHANGELOG.md` from git history with one command.

## Setup

1. Copy `changelog.sh` into the root of any git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md` before committing it.

## Behavior

- Uses the latest git tag as the starting point.
- Falls back to the full commit history when no tag exists.
- Supports `--since TAG_OR_REF` for manual ranges.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Links commits automatically when the repository has a GitHub `origin` remote.

## Examples

```bash
bash changelog.sh
bash changelog.sh --output docs/CHANGELOG.md
bash changelog.sh --since v1.2.0
```

## Commit Categories

The script understands conventional commit prefixes first:

- `feat`, `add`, `create`, `implement`, `support` -> `Added`
- `fix`, `bugfix`, `resolve`, `patch` -> `Fixed`
- `remove`, `delete`, `drop`, `deprecate` -> `Removed`
- `chore`, `ci`, `build`, `docs`, `style`, `test`, `refactor`, `perf`, `update`, `improve` -> `Changed`

When a commit is not conventional, it uses simple keyword matching and otherwise places the commit under `Changed`.
