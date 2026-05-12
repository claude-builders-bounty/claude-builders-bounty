# Generate Changelog

Create a structured `CHANGELOG.md` from git history using a dependency-free bash script.

## Setup

1. Copy `generate-changelog/changelog.sh` into any git repository.
2. Run `bash changelog.sh` from inside that repository.
3. Review the generated `CHANGELOG.md` before committing it.

## What It Does

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- Reads commits from that tag through `HEAD`; if no tag exists, it uses the full repository history.
- Categorizes non-merge commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown `CHANGELOG.md`.

## Categorization Rules

- `Added`: `feat:`, `add:`, `added:`, `implement:`
- `Fixed`: `fix:`, `fixed:`, `bug:`, `bugfix:`, `patch:`
- `Removed`: `remove:`, `removed:`, `delete:`, `deleted:`, `drop:`, `deprecate:`
- `Changed`: everything else, including docs, chore, refactor, test, build, and plain commit messages

Conventional commit scopes and breaking-change markers are stripped from the visible bullet text. For example, `feat(api)!: add export endpoint` becomes `add export endpoint`.

## Usage

```bash
bash generate-changelog/changelog.sh
```

To write to a custom file:

```bash
bash generate-changelog/changelog.sh RELEASE_NOTES.md
```

## Sample Output

See `sample-output.md` for output generated against this repository.
