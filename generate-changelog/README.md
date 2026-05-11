# Generate Changelog

Generate a structured `CHANGELOG.md` from Git commits since the latest tag.

## Setup

1. Copy `changelog.sh` and `generate-changelog/` into any Git repository.
2. Run `bash changelog.sh` from that repository's root.
3. Review the generated `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
```

Optionally pass a custom output path:

```bash
bash changelog.sh docs/CHANGELOG.md
```

## Categories

The script sorts commit subjects into:

- `Added`: `feat`, `add`, `create`, and similar commit subjects.
- `Fixed`: `fix`, `bug`, `resolve`, `repair`, and similar commit subjects.
- `Changed`: `change`, `refactor`, `perf`, `docs`, `test`, `build`, `ci`, `chore`, `update`, and uncategorized subjects.
- `Removed`: `remove`, `delete`, `drop`, `deprecate`, and similar commit subjects.

If the repository has no tags, the script uses all commits reachable from `HEAD`.
