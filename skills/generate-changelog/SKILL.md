---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when a user asks for `/generate-changelog`, asks to create a changelog from git history, or wants release notes grouped by change type.

## Workflow

1. Run `bash scripts/changelog.sh` from the repository root to write `CHANGELOG.md`.
2. Use `--from REF` to override the default latest-tag range, or `--stdout` to preview without writing.
3. Review the generated Added, Fixed, Changed, and Removed sections before committing.

## Examples

```bash
bash scripts/changelog.sh
bash scripts/changelog.sh --from v1.2.0 --version v1.3.0
bash scripts/changelog.sh --stdout --to HEAD
```
