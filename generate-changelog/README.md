# Generate Changelog

Generate a Markdown `CHANGELOG.md` from the Git commits since the latest tag.

## Setup

1. Copy `changelog.sh` and the `generate-changelog/` folder into a Git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
```

Optional flags:

```bash
bash changelog.sh --since v1.2.0
bash changelog.sh --output docs/CHANGELOG.md
bash changelog.sh --include-merges
```

The script groups commits into `Added`, `Fixed`, `Changed`, and `Removed` sections using common conventional-commit prefixes and plain-English commit verbs. Ambiguous commit subjects fall back to `Changed`.

## Testing

```bash
bash generate-changelog/tests/changelog_test.sh
```

## Notes

- If the repository has tags, the script uses the latest tag as the start point.
- If the repository has no tags, it generates a changelog from the full history.
- If a changelog already exists, the new unreleased section is prepended and the older content is preserved.

See [`sample-output.md`](sample-output.md) for an example generated from a real GitHub repository.
