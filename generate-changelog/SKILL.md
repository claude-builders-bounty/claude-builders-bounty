---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when the user asks to generate or refresh a changelog from git history.

## Workflow

1. Confirm you are inside the target git repository.
2. Run:

   ```bash
   bash changelog.sh
   ```

3. Review `CHANGELOG.md` for wording before committing it.

## Behavior

- The script fetches tags from `origin` when a remote exists.
- It uses the latest reachable tag as the release boundary.
- If the repository has no tags, it uses the full history.
- It groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- It keeps short commit hashes in each entry for traceability.

## Options

Use a custom output path:

```bash
CHANGELOG_OUTPUT=docs/CHANGELOG.md bash changelog.sh
```

Skip tag fetching in offline or hermetic environments:

```bash
CHANGELOG_FETCH_TAGS=0 bash changelog.sh
```
