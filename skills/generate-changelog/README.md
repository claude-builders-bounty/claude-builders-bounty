# Generate Changelog

Generate a structured `CHANGELOG.md` from git history since the latest tag.

## Setup

1. Copy `skills/generate-changelog/` into your repository.
2. Run `bash skills/generate-changelog/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Example

```bash
bash skills/generate-changelog/changelog.sh --version 1.2.0
```

The script auto-categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`. It uses the latest git tag as the starting point. If no tags exist, it uses all commits.
