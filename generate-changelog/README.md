# Generate Changelog

Creates a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy `changelog.sh` into a git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh --output CHANGELOG.md
bash changelog.sh --since v1.2.0 --output CHANGELOG.md
```

The script groups commit subjects into `Added`, `Fixed`, `Changed`, and
`Removed`, and includes short SHAs for traceability.
