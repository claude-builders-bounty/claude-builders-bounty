# Generate Changelog Skill

Create a structured `CHANGELOG.md` from the current git repository.

## Usage

```bash
bash changelog.sh
```

Optional flags:

```bash
bash changelog.sh --since v1.2.0 --output CHANGELOG.md
bash changelog.sh --repo /path/to/repo --output /tmp/CHANGELOG.md
```

## What it does

- Finds commits since the latest git tag. If no tag exists, it uses repository history.
- Skips merge commits.
- Groups commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep-a-Changelog style `CHANGELOG.md`.

## Notes

This is intentionally dependency-free Bash so it can run in small repos and CI jobs.
Review the generated file before release notes are published.
