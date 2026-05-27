# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `changelog.sh` and `tools/generate_changelog/generate_changelog.py` into a git repository.
2. Run `bash changelog.sh --repo . --output CHANGELOG.md`.
3. Review the generated `Added`, `Fixed`, `Changed`, and `Removed` sections.

## Options

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md --version v1.2.0
```

- `--repo`: target git repository, defaults to the current directory
- `--output`: changelog output path, defaults to `CHANGELOG.md`
- `--version`: heading label, defaults to `Unreleased`
- `--no-fetch`: skip `git fetch --tags`

The generator uses the latest git tag as the baseline. If a repository has no tags, it uses the full history.
