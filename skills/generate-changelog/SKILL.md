# Generate Changelog

Use this skill when asked to create or refresh a project changelog from git history.

## Workflow

1. Run `bash changelog.sh` from the target git repository.
2. Review the generated `CHANGELOG.md` categories for accuracy.
3. Commit the changelog with the script output or paste the `--stdout` output where requested.

## Options

- `bash changelog.sh --stdout` prints the changelog without writing a file.
- `bash changelog.sh --output docs/CHANGELOG.md` writes to a custom path.
- `bash changelog.sh --since v1.2.3` overrides automatic last-tag detection.

## Behavior

The script finds commits since the latest git tag by default, skips merge commits, and categorizes entries into `Added`, `Fixed`, `Changed`, and `Removed`.
