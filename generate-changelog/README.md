# Generate Changelog

## Setup in 3 steps

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Example commands

```bash
bash changelog.sh
bash changelog.sh --since v1.0.0 --output CHANGELOG.md
```

## Acceptance criteria coverage

- `/generate-changelog` equivalent is represented as `bash changelog.sh`.
- Fetches commits since the latest git tag, or all history if there is no tag.
- Groups output into `Added`, `Fixed`, `Changed`, and `Removed`.
- Outputs valid Markdown to `CHANGELOG.md`.
- Includes tested sample output in `sample-output.md`.
- Setup is 3 steps.
