# Generate Changelog

Use this skill when a project needs a structured `CHANGELOG.md` generated from
git history.

## Workflow

1. Run `bash changelog.sh` from the repository root.
2. Review the `Added`, `Fixed`, `Changed`, and `Removed` sections.
3. Commit the generated `CHANGELOG.md` with the release changes.

## Options

- `--range v1.0.0..HEAD` uses an explicit git revision range.
- `--output path/to/CHANGELOG.md` writes to a custom output path.
- `--version v1.1.0` sets the release heading.
