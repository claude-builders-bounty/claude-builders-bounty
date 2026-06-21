---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, release notes, or a structured changelog from git history.

## Workflow

1. From the project root, run:

   ```bash
   bash changelog.sh
   ```

2. Review `CHANGELOG.md` for any wording that should be clarified before release.
3. Commit the generated `CHANGELOG.md` with the release changes.

## Behavior

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Reads commits after that tag; if no tag exists, it reads all commits.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown `CHANGELOG.md` suitable for release review.

## Options

```bash
bash changelog.sh --version v1.2.0
bash changelog.sh --since v1.1.0
bash changelog.sh --stdout
```
