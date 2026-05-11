# Generate Changelog from Git History

A tiny Bash utility that creates a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup in 3 steps

1. Copy `generate-changelog/changelog.sh` into any git repository.
2. Run `chmod +x changelog.sh` if needed.
3. Run `./changelog.sh` or `./changelog.sh CUSTOM_CHANGELOG.md`.

## What it does

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Reads commits from `latest-tag..HEAD`; if there are no tags, reads the whole history.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed` using Conventional Commit prefixes and common keywords.
- Writes a clean Markdown changelog.

## Category mapping

- `feat:`, `feature:`, `add:` → Added
- `fix:`, `bug:`, `hotfix:` → Fixed
- `remove:`, `delete:`, `deprecate:` → Removed
- `change:`, `refactor:`, `perf:`, `docs:`, `chore:`, `ci:`, `test:` → Changed

## Example

```bash
./generate-changelog/changelog.sh SAMPLE_OUTPUT.md
```

See [`SAMPLE_OUTPUT.md`](./SAMPLE_OUTPUT.md) for output generated against this repository.
