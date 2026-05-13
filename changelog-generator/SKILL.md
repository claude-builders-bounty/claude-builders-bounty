# Generate Changelog

Use this skill when a project needs a structured changelog generated from git history.

## Command

Run the included script from the root of any git repository:

```bash
bash changelog.sh
```

The script writes `CHANGELOG.md` by default. Set `CHANGELOG_FILE` to write to a different path, or `CHANGELOG_RANGE` to summarize an explicit git revision range.

## Workflow

1. Copy `changelog.sh` into the target repository.
2. Run `bash changelog.sh`.
3. Review `CHANGELOG.md` and adjust wording before publishing.

## Classification

The script maps common commit prefixes and keywords into:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

Commits that do not clearly match another category are placed under `Changed`.
