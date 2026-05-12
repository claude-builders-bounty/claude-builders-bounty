# Generate Changelog

Generate a structured `CHANGELOG.md` from git history with no external dependencies.

## Setup

1. Copy `generate-changelog/` into a git repository.
2. Run `bash generate-changelog/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## What It Does

- Detects the latest git tag and uses commits after that tag.
- Falls back to full history if the repository has no tags.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Preserves older changelog content below the new generated section.

## Examples

```bash
bash generate-changelog/changelog.sh
bash generate-changelog/changelog.sh --dry-run
bash generate-changelog/changelog.sh --since v1.0.0 --output RELEASE_NOTES.md
```
