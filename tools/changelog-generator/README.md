# Changelog Generator

Generate a structured `CHANGELOG.md` from the current repository's git history.

## Setup

1. Copy `changelog.sh` into the repository you want to document.
2. Run `bash changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` before committing it.

## What It Does

- Uses commits since the latest git tag, or the full history when no tag exists.
- Skips merge commits so the output stays focused on authored changes.
- Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes Markdown output to `CHANGELOG.md` by default, or to a custom file path passed as the first argument.

## Example

```bash
bash tools/changelog-generator/changelog.sh
bash tools/changelog-generator/changelog.sh docs/CHANGELOG.preview.md
```

