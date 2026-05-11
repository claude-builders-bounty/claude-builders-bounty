# Generate Changelog

Dependency-free Bash generator for creating a structured `CHANGELOG.md` from git history since the latest tag.

## Setup

1. Copy `skills/generate-changelog/changelog.sh` into any git repository.
2. Run `bash changelog.sh` or `bash changelog.sh --output docs/CHANGELOG.md`.
3. Review the generated changelog before committing it.

## Categories

- `Added`: `feat`, `feature`, `add`, or subjects starting with `add`
- `Fixed`: `fix`, `bugfix`, `hotfix`, `patch`, or subjects starting with `fix`
- `Removed`: `remove`, `delete`, `drop`, `deprecate`, or matching subject starts
- `Changed`: everything else, including `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, and `style`

## Test

```bash
bash skills/generate-changelog/tests/test_changelog.sh
```
