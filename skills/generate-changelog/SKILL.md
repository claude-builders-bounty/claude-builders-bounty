# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, wants a `CHANGELOG.md`, or needs release notes generated from git history.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run `bash changelog.sh` from this package, or copy `changelog.sh` and `scripts/changelog.sh` into the target repository.
3. Review the generated `CHANGELOG.md` for project-specific wording before committing it.

## Behavior

The script:

- detects the latest git tag with `git describe --tags --abbrev=0`;
- reads commits after that tag, or all commits when the repository has no tags;
- categorizes entries into `Added`, `Fixed`, `Changed`, and `Removed`;
- writes a Markdown `CHANGELOG.md` suitable for a pull request or release draft.

## Command

```bash
bash changelog.sh
```

Useful options:

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md
bash changelog.sh --since v1.2.0 --version 1.3.0
bash changelog.sh --dry-run
```
