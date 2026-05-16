# Generate Changelog

## Setup

1. Use Python 3.10+ in any git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` before committing it.

## Usage

```bash
bash changelog.sh
```

Optional flags:

```bash
bash changelog.sh --version v1.2.0
bash changelog.sh --output docs/CHANGELOG.md
bash changelog.sh --stdout
```

## Behavior

- Reads commits since the latest git tag.
- Falls back to the full history when the repository has no tag.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a properly formatted `CHANGELOG.md`.
