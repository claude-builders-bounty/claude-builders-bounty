# Generate Changelog

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy `tools/generate-changelog` into your repository.
2. Run `bash tools/generate-changelog/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

```bash
bash tools/generate-changelog/changelog.sh
```

Optional flags:

```bash
bash tools/generate-changelog/changelog.sh --since v1.2.0 --output CHANGELOG.md
bash tools/generate-changelog/changelog.sh --repo /path/to/repo
```

## Categorization

The generator reads non-merge commits from `{latest-tag}..HEAD` and groups them into:

- `Added`: `feat:`, `feature:`, `add:`, or subjects starting with `add`
- `Fixed`: `fix:`, `bugfix:`, `hotfix:`, or subjects containing `fix` / `bug`
- `Removed`: `remove:`, `delete:`, `drop:`, or matching subject prefixes
- `Changed`: everything else

The output follows a Keep a Changelog-style layout and includes the short commit SHA for traceability.
