# Generate Changelog Skill

## Setup

1. Copy `skills/generate-changelog/` into your repository.
2. Run `bash skills/generate-changelog/scripts/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Categories

- `Added`: `feat`, `add`, `new`
- `Fixed`: `fix`, `bug`, `patch`
- `Changed`: `change`, `refactor`, `perf`, `docs`, `chore`, `build`, `ci`, `test`, `style`
- `Removed`: `remove`, `delete`, `drop`, `deprecate`

Commits that do not match a category are listed under `Changed`.
