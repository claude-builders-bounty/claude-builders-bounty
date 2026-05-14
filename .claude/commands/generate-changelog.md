# /generate-changelog

Generate a structured `CHANGELOG.md` from the current repository's git history.

Run this command from the repository root:

```bash
bash changelog.sh
```

Behavior:

- Finds the latest reachable git tag and reads commits from that tag to `HEAD`.
- Falls back to the full history when the repository has no tags.
- Groups commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Prepends the generated release section to `CHANGELOG.md`.

Use `CHANGELOG_OUTPUT=docs/CHANGELOG.md bash changelog.sh` when the project keeps its changelog somewhere else.
