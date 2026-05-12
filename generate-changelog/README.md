# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Behavior

The script reads non-merge commit subjects since the latest git tag. If the repository has no tags, it reads all commits reachable from `HEAD`.

Commits are grouped into:

* `Added`: `feat:`, `add:`, `added:`, `new:`
* `Fixed`: `fix:`, `bug:`, `bugfix:`, `hotfix:`, `patch:`
* `Changed`: `change:`, `refactor:`, `perf:`, `docs:`, `chore:`, `build:`, `ci:`, `test:`, `style:`, and uncategorized commits
* `Removed`: `remove:`, `removed:`, `delete:`, `deleted:`, `drop:`, `dropped:`, `deprecate:`, `deprecated:`

You can pass a custom output path:

```sh
bash changelog.sh RELEASE_NOTES.md
```
