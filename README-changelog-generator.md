# Git Changelog Generator

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup / usage

1. Copy `changelog.sh` into any git repo.
2. Run `bash changelog.sh` (or `bash changelog.sh RELEASE_NOTES.md`).
3. Review the generated Added / Fixed / Changed / Removed sections before release.

## Categorization

The script reads non-merge commits since the latest tag (`git describe --tags --abbrev=0`). If no tag exists, it uses the full repo history.

- `feat`, `feature`, `add` → Added
- `fix`, `bugfix`, `hotfix` → Fixed
- `remove`, `delete`, `drop` → Removed
- `refactor`, `change`, `update`, `docs`, `chore`, `ci`, `test` → Changed
- uncategorized commits → Other
